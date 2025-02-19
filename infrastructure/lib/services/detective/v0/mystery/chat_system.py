import json
import re
from typing import Generator, List

import mystery.constants as constants
from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.context_basket.model import ContextBasket, DataRequest
from mystery.data_agent import DataAgent
from mystery.util import count_tokens

from .mrkl.open_ai import OpenAIChat
from .mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole


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

    def run(
        self,
        message: str,
        page_ids: List[str] = None
    ) -> Generator[str, None, None]:
        print('[ChatSystem] Running...')
        yield '[THOUGHT]Determining if I need more information...'
        requests = self._generate_requests(message)
        if not requests:
            yield (
                '[THOUGHT]I don\'t need more information. Thinking about my '
                'response...'
            )
            response = self._respond_without_context(message)
            yield response
            return
        if len(requests) > 4:
            response = ('Your message requires more information than I can '
                        'handle. Please try to be more specific.')
            yield response
            return
        baskets: List[ContextBasket] = []
        for update in self._retrieve_context(
            requests, 
            baskets, 
            page_ids=page_ids
        ):
            yield '[THOUGHT]' + update
        yield '[THOUGHT]Synthesizing information and thinking about my response...'
        context = ''
        for basket in baskets:
            context += str(basket)
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
            role=ChatPromptMessageRole.SYSTEM,
            content=constants.CHAT_SYSTEM_SYSTEM_MESSAGE
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER,
            content=message
        )
        prompt = ChatPrompt([system_message, user_message])
        llm_response = self._gpt_4.predict(prompt)
        requests = _parse_llm_response_for_requests(llm_response)
        print(f'[ChatSystem] Requests generated! {requests}'.replace('\n', '||'))
        return requests

    def _retrieve_context(
        self,
        requests: List[str],
        baskets: List[ContextBasket],
        page_ids: List[str] = None,
    ) -> Generator[str, None, None]:
        max_tokens = constants.MAX_CONTEXT_SIZE // len(requests)

        print('[ChatSystem] Retrieving context...')
        for request in requests:
            yield f'Researching: "{request}"...'
            data_request = DataRequest(
                request=request,
                page_ids=page_ids,
                max_tokens=max_tokens
            )
            response = self._data_agent.generate_context(data_request)
            baskets.append(response.context_basket)
            
        print('[ChatSystem] Context retrieved!')
        return

    def _respond_with_context(self, message: str, context: str) -> str:
        print(f'[ChatSystem] Producing response with context... {context}'.replace('\n', '||'))
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        context_size = count_tokens(context, self._chat_gpt.encoding_name)
        prompt_size = message_size + context_size
        if prompt_size > constants.MAX_PROMPT_SIZE:
            response = ('I received too many tokens to produce a proper '
                        'response.')
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM,
                content=constants.RESPOND_WITH_CONTEXT_SYSTEM_MESSAGE.format(
                    context=context
                )
            )
            user_message = ChatPromptMessage(
                role=ChatPromptMessageRole.USER,
                content=message
            )
            prompt = ChatPrompt([system_message, user_message])
            response = self._chat_gpt.predict(prompt)
        print('[ChatSystem] Produced response with context!')
        return response

    def _respond_without_context(self, message: str) -> str:
        print('[ChatSystem] Producing response without information...')
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        if message_size > constants.MAX_PROMPT_SIZE:
            response = ('I received too many tokens to produce a proper '
                        'response.')
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM,
                content=constants.RESPOND_WITHOUT_CONTEXT_SYSTEM_MESSAGE
            )
            user_message = ChatPromptMessage(
                role=ChatPromptMessageRole.USER,
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
        print(f'[ChatSystem] LLM response: {llm_response}'.replace('\n', '||'))
        return []
    stringified_list = match.group(0)
    requests = json.loads(stringified_list)
    return requests