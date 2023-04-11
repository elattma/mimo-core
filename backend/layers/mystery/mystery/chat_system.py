import json
import re
from typing import Dict, Generator, List

from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.context_basket.model import ContextBasket
from mystery.context_basket.weaver import BasketWeaver
from mystery.data_agent import DataAgent
from mystery.override import Override
from mystery.util import count_tokens

from .mrkl.open_ai import OpenAIChat
from .mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole

MAX_TOKENS = 4000

GENERATE_REQUESTS_SYSTEM_MESSAGE_CONTENT = '''You are ChatGPT and you only know everything that ChatGPT was trained on.
You are chatting with a user that assumes you know everything about their company and its data.
You have access to a database of all the company's data that can be queried with natural language.
Your job is to think about what parts of the user's message require information from the database to answer.
Then, you should create a list of natural language requests that describe the information you need from the database.
Remember that the database only contains information about the company. You should not generate requests that are about common knowledge or things you already know.
Requests should be a specific description of the information you need from the database. They should not include the tasks that the user has asked you to perform based on the information.
The list of requests should look like ["request1", "request2", ..., "requestN"].

Here are some examples to further guide your thinking:
EXAMPLE 1
Message: Summarize the complaints from my last 5 Zendesk tickets
Requests: ["last 5 Zendesk tickets"]

EXAMPLE 2
Message: How many days of PTO can I take this year?
Requests: ["vacation policy"]

EXAMPLE 3
Message: What is the capital of Italy?
Requests: []
'''

RESPOND_WITH_CONTEXT_SYSTEM_MESSAGE_CONTENT = '''Respond to the user's message. Use the information below as context.
---------
{context}'''

RESPOND_WITHOUT_CONTEXT_SYSTEM_MESSAGE_CONTENT = '''Respond to the user's message.'''


class ChatSystem:
    _gpt_4: OpenAIChat = None
    _chat_gpt: OpenAIChat = None
    _data_agent: DataAgent = None

    def __init__(self, owner: str, graph_db: Neo4j, vector_db: Pinecone,
                 openai: OpenAI) -> None:
        print('[ChatSystem] Initializing...')
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAI = openai
        if not self._gpt_4:
            self._gpt_4 = OpenAIChat(client=openai, model='gpt-4')
        if not self._chat_gpt:
            self._chat_gpt = OpenAIChat(client=openai, model='gpt-3.5-turbo')
        if not self._data_agent:
            self._data_agent = DataAgent(
                owner=self._owner,
                graph_db=self._graph_db,
                vector_db=self._vector_db,
                openai=self._openai_client
            )
        print('[ChatSystem] Initialized!')

    def run(self, message: str, overrides: List[Override] = None) -> Generator[str, None, None]:
        print('[ChatSystem] Running...')
        yield 'Interpreting message...'
        requests = self._generate_requests(message)
        if not requests:
            response = self._respond_without_context(message)
            yield '' + response
            return
        baskets: List[ContextBasket] = []
        for update in self._retrieve_context(requests, baskets, overrides):
            yield update
        yield 'Synthesizing information...'
        context = self._stringify_context(baskets)
        yield 'Responding to message...'
        response = self._respond_with_context(
            message,
            context
        )
        print('[ChatSystem] Ran!')
        yield response
        return

    def _generate_requests(self, message: str) -> List[str]:
        print('[ChatSystem] Generating requests...')
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=GENERATE_REQUESTS_SYSTEM_MESSAGE_CONTENT
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=message
        )
        prompt = ChatPrompt([system_message, user_message])
        llm_response = self._gpt_4.predict(prompt)
        requests = _parse_llm_response_for_requests(llm_response)
        print('[ChatSystem] Requests generated!')
        print(requests)
        return requests

    def _retrieve_context(
        self,
        requests: List[str],
        baskets: List[ContextBasket],
        overrides: List[Override] = None
    ) -> Generator[str, None, None]:
        print('[ChatSystem] Retrieving context...')
        for request in requests:
            yield f'Looking up: "{request}"'
            basket = self._data_agent.generate_context(request, overrides)
            if basket:
                baskets.append(basket)
        print('[ChatSystem] Context retrieved!')
        return

    def _stringify_context(
        self,
        baskets: List[ContextBasket]
    ) -> str:
        print('[ChatSystem] Stringifying context...')
        context = ''
        for basket in baskets:
            BasketWeaver.minify_context_basket(
                context_basket=basket,
                limit_tokens=MAX_TOKENS // len(baskets)
            )
            context += f'{basket.request.text}\n'
            context += '--------\n'
            context += '\n'.join([context.translated
                                  for context in basket.contexts])
        print('[ChatSystem] Stringified context!')
        print(context)
        return context

    def _respond_with_context(self, message: str, context: str) -> str:
        print('[ChatSystem] Producing response with information...')
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        context_size = count_tokens(context, self._chat_gpt.encoding_name)
        if message_size + context_size > MAX_TOKENS:
            response = 'I received too many tokens to produce a proper response.'
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM.value,
                content=RESPOND_WITH_CONTEXT_SYSTEM_MESSAGE_CONTENT.format(
                    context=context
                )
            )
            user_message = ChatPromptMessage(
                role=ChatPromptMessageRole.USER.value,
                content=message
            )
            prompt = ChatPrompt([system_message, user_message])
            response = self._chat_gpt.predict(prompt)
        print('[ChatSystem] Produced response with information!')
        return response

    def _respond_without_context(self, message: str) -> str:
        print('[ChatSystem] Producing response without information...')
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        if message_size > MAX_TOKENS:
            response = 'I received too many tokens to produce a proper response.'
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM.value,
                content=RESPOND_WITHOUT_CONTEXT_SYSTEM_MESSAGE_CONTENT
            )
            user_message = ChatPromptMessage(
                role=ChatPromptMessageRole.USER.value,
                content=message
            )
            prompt = ChatPrompt([system_message, user_message])
            response = self._chat_gpt.predict(prompt)
        print('[ChatSystem] Produced response without information!')
        return response


def _parse_llm_response_for_requests(llm_response: str) -> List[str]:
    match = re.search(r'\[[\s\S]*\]', llm_response, re.DOTALL)
    if not match:
        print('[ChatSystem] Failed to parse LLM response')
        print('[ChatSystem]: LLM response:')
        print(llm_response)
        return []
    stringified_list = match.group(0)
    requests = json.loads(stringified_list)
    return requests
