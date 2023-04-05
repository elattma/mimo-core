import json
import re
from typing import Dict, Generator, List

from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from tiktoken import Encoding, get_encoding

from .mrkl.open_ai import OpenAIChat
from .mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole
from .qa_agent import Answer, QuestionAnswerAgent

MAX_TOKENS = 4000

GENERATE_REQUESTS_SYSTEM_MESSAGE_CONTENT = '''You are ChatGPT and you only know everything that ChatGPT was trained on.
You are chatting with a user that assumes you know everything about their company and its data.
You have access to a database of all the company's data that can be queried with natural language.
Your job is to think about what parts of the user's message require information from the database to answer.
Then, you should create a list of natural language requests that describe the information you need from the database.
Remember that the database only contains information about the company. You should not generate requests that are about common knowledge or things you already know.
The list of requests should look like ["request1", "request2", ..., "requestN"].

Here are some examples to further guide your thinking:
EXAMPLE 1
Message: What are the most common complaints from our last 10 Zendesk tickets?
Requests: ["last 10 Zendesk tickets"]

EXAMPLE 2
Message: How many days of PTO can I take this year?
Requests: ["vacation policy"]

EXAMPLE 3
Message: What is the capital of Italy?
Requests: []
'''

CONDENSE_CONTEXT_SYSTEM_MESSAGE_CONTENT = '''Pretend you are an Information Scrubber.
Your job is to look at raw information and based on a message you are given, return a sanitized version of the information containing the most relevant information to the message.

Here is the raw information:
--------
{raw_context}'''

RESPOND_WITH_INFORMATION_SYSTEM_MESSAGE_CONTENT = '''Respond to the user's message. Use the information below as context.
---------
{context}'''

RESPOND_WITHOUT_INFORMATION_SYSTEM_MESSAGE_CONTENT = '''Respond to the user's message.'''

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

    def run(self, message: str) -> str:
        print('[ChatSystem] Running...')
        requests = self._generate_requests(message)
        if not requests:
            response = self._respond_without_information(message)
            return response
        information = self._retrieve_information(requests)
        context = self._information_to_context(information)
        response = self._respond_with_information(
            message,
            context
        )
        print('[ChatSystem] Ran!')
        return response

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
    
    def _retrieve_information(self,
                              requests: List[str]) -> Dict[str, ContextBasket]:
        print('[ChatSystem] Retrieving information...')
        information = {}
        for request in requests:
            context_basket = self._data_agent.generate_context(request)
            information[request] = context_basket
        print('[ChatSystem] Information retrieved!')
        print(information)
        return information
    
    def _information_to_context(
        self,
        information: Dict[str, ContextBasket]
    ) -> str:
        print('[ChatSystem] Converting information to context...')
        context = ''
        for request, context_basket in information.items():
            context_for_request = self._condense_context(
                request,
                context_basket
            )
            context += context_for_request
            context += '\n\n'
        print('[ChatSystem] Converted information to context!')
        print(context)
        return context

    def _condense_context(
        self,
        request: str,
        context_basket: ContextBasket
    ) -> str:
        print(f'[ChatSystem] Condensing context for request: "{request}"')
        raw_context = '\n'.join(
            [context.content for context in context_basket]
        )
        system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM.value,
                content=CONDENSE_CONTEXT_SYSTEM_MESSAGE_CONTENT.format(
                    raw_context=raw_context
                )
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=request
        )
        prompt = ChatPrompt([system_message, user_message])
        condensed_context = self._chat_gpt.predict(prompt)
        print('[ChatSystem] Condensed context!')
        return condensed_context

    def _respond_with_information(self, message: str, context: str) -> str:
        print('[ChatSystem] Producing response with information...')
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        context_size = count_tokens(context, self._chat_gpt.encoding_name)
        if message_size + context_size > MAX_TOKENS:
            response = 'I received too many tokens to produce a proper response.'
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM.value,
                content=RESPOND_WITH_INFORMATION_SYSTEM_MESSAGE_CONTENT.format(
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
    
    def _respond_without_information(self, message: str) -> str:
        print('[ChatSystem] Producing response without information...')
        message_size = count_tokens(message, self._chat_gpt.encoding_name)
        if message_size > MAX_TOKENS:
            response = 'I received too many tokens to produce a proper response.'
        else:
            system_message = ChatPromptMessage(
                role=ChatPromptMessageRole.SYSTEM.value,
                content=RESPOND_WITHOUT_INFORMATION_SYSTEM_MESSAGE_CONTENT
            )
            user_message = ChatPromptMessage(
                role=ChatPromptMessageRole.USER.value,
                content=message
            )
            prompt = ChatPrompt([system_message, user_message])
            response = self._chat_gpt.predict(prompt)
        print('[ChatSystem] Produced response without information!')
        return response

    # def run(self, message: str) -> Generator[str, None, None]:
    #     questions: List[str] = self._generate_questions_from_message(message)
    #     if questions:
    #         questions_str = '\n'.join(f'{i}. {q}' for i, q in enumerate(questions, 1))
    #         yield ('Before we can respond to your message, we need to find '
    #                f'answers to the following questions:\n{questions_str}')
    #     qas: Dict[str, Answer] = {}
    #     for question in questions:
    #         yield f'Finding an answer to: {question}'
    #         answer = self._qa_agent.run(question)
    #         yield 'Answer found!'
    #         qas[question] = answer
    #     if questions:
    #         yield 'I now have all the information I need to respond to your message.'
    #     response = self._respond_using_qas(message, qas)
    #     yield response
    
    # def debug_run(self, message: str) -> str:
    #     print('[ChatSystem] Running debug_run...\n')
    #     print('[ChatSystem] Received message...')
    #     print(message, '\n')
    #     print('[ChatSystem] Generating questions...')
    #     questions: List[str] = self._generate_questions_from_message(message)
    #     print(questions, '\n')
    #     qas: Dict[str, Answer] = {}
    #     for question in questions:
    #         print('[ChatSystem] Running QuestionAnswerAgent on question...')
    #         answer = self._qa_agent.debug_run(question)
    #         print('[ChatSystem] Answer received...')
    #         print(answer, '\n')
    #         qas[question] = answer
    #     print('[ChatSystem] Generating response...')
    #     response = self._respond_using_qas(message, qas)
    #     print(response, '\n')
    #     return response
    
    # def _generate_questions_from_message(self, message: str) -> str:
    #     system_message = ChatPromptMessage(
    #         role=ChatPromptMessageRole.SYSTEM.value,
    #         content=GENERATE_QUESTIONS_SYSTEM_MESSAGE
    #     )
    #     user_message = ChatPromptMessage(
    #         role=ChatPromptMessageRole.USER.value,
    #         content=message
    #     )
    #     prompt = ChatPrompt([system_message, user_message])
    #     llm_response = self._gpt_4.predict(prompt)
    #     try:
    #         questions = _parse_llm_response_for_questions(llm_response)
    #         return questions
    #     except ValueError:
    #         # Try again one more time with a scolding message.
    #         assistant_message = ChatPromptMessage(
    #             role=ChatPromptMessageRole.ASSISTANT.value,
    #             content=llm_response,
    #         )
    #         user_message_scold = ChatPromptMessage(
    #             role=ChatPromptMessageRole.USER.value,
    #             content='You didn\'t follow the format of the examples. Try again.',
    #         )
    #         prompt = ChatPrompt([system_message, user_message,
    #                              assistant_message, user_message_scold])
    #         llm_response = self._chat_gpt.predict(prompt)
    #         try:
    #             questions = _parse_llm_response_for_questions(llm_response)
    #             return questions
    #         except ValueError:
    #             return []

    # def _respond_using_qas(self, message: str, qas: Dict[str, Answer]) -> str:
    #     if qas:
    #         formatted_qas = '\n\n'.join(
    #             [f'Question: {question}\nAnswer: {answer.content}'
    #              for question, answer in qas.items()])
    #         system_message_content = RESPONSE_SYSTEM_MESSAGE_WITH_QAS.format(
    #             formatted_qas=formatted_qas
    #         )
    #     else:
    #         system_message_content = RESPONSE_SYSTEM_MESSAGE_WITHOUT_QAS
    #     token_count = count_tokens(system_message_content,
    #                                self._chat_gpt.encoding_name)
    #     if token_count > MAX_TOKENS:
    #         return 'I received context that was too long to respond to.'
    #     system_message = ChatPromptMessage(
    #         role=ChatPromptMessageRole.SYSTEM.value,
    #         content=system_message_content
    #     )
    #     user_message = ChatPromptMessage(
    #         role=ChatPromptMessageRole.USER.value,
    #         content=message
    #     )
    #     prompt = ChatPrompt([system_message, user_message])
    #     response = self._chat_gpt.predict(prompt)
    #     return response
    
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
