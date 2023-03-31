import re
from typing import Dict, Generator, List

from tiktoken import Encoding, get_encoding

from app.client._neo4j import Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone
from app.mrkl.open_ai import OpenAIChat
from app.mrkl.prompt import ChatPrompt, ChatPromptMessage, ChatPromptMessageRole
from app.mystery.qa_agent import Answer, QuestionAnswerAgent

MAX_TOKENS = 3000

GENERATE_QUESTIONS_SYSTEM_MESSAGE = '''You are ChatGPT and you only know everything that GPT-4 was trained on.
You are chatting with a user that assumes you know everything about their company and its data. But, you don't know everything.
Your job is to come up with a list of questions based on what you need to know more about to respond to the user.
The questions will be used to fetch information from a database, they will not be directed to the user. So, do not ask questionst that are intended to be answered by the user.
The list of questions should be in the format [{question1} {question2} ... {questionN}}]
The examples below will show you how to think. Follow the format of the examples.
---------
EXAMPLES:
Input: Tell me about Troy's performance last quarter and what he's working on this quarter.
Output: [{How did Troy perform last quarter?} {What is Troy working on this quarter?}]

Input: How can we solve the problems our customers are facing with our API?
Output: [{What problems are our customers facing with our API?}]'''

RESPONSE_SYSTEM_MESSAGE_WITH_QAS = '''Respond to the user's message. Use the answers to the questions below to help you where needed.
---------
{formatted_qas}'''

RESPONSE_SYSTEM_MESSAGE_WITHOUT_QAS = '''Respond to the user's message.'''

class ChatSystem:
    _gpt_4: OpenAIChat = None
    _chat_gpt: OpenAIChat = None
    _qa_agent: QuestionAnswerAgent = None
    _chat_encoding: Encoding = None

    def __init__(self, owner: str, graph_db: Neo4j, vector_db: Pinecone,
                 openai: OpenAI, integrations: List[str]) -> None:
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAI = openai
        self._integrations = integrations
        if not self._gpt_4:
            self._gpt_4 = OpenAIChat(client=openai, model='gpt-4')
        if not self._chat_gpt:
            self._chat_gpt = OpenAIChat(client=openai, model='gpt-3.5-turbo')
        if not self._qa_agent:
            self._qa_agent = QuestionAnswerAgent(
                owner=self._owner,
                graph_db=self._graph_db,
                vector_db=self._vector_db,
                openai=self._openai_client
            )
        if not self._chat_encoding:
            self._chat_encoding = get_encoding(
                self._gpt_4.encoding_name
            )

    def run(self, message: str) -> Generator[str, None, None]:
        questions: List[str] = self._generate_questions_from_message(message)
        if questions:
            questions_str = '\n'.join(f'{i}. {q}' for i, q in enumerate(questions, 1))
            yield ('Before we can respond to your message, we need to find '
                   f'answers to the following questions:\n{questions_str}')
        qas: Dict[str, Answer] = {}
        for question in questions:
            yield f'Finding an answer to: {question}'
            answer = self._qa_agent.run(question, self._integrations)
            yield 'Answer found!'
            qas[question] = answer
        if questions:
            yield 'I now have all the information I need to respond to your message.'
        response = self._respond_using_qas(message, qas)
        yield response
    
    def debug_run(self, message: str) -> str:
        print('[ChatSystem] Running debug_run...\n')
        print('[ChatSystem] Received message...')
        print(message, '\n')
        print('[ChatSystem] Generating questions...')
        questions: List[str] = self._generate_questions_from_message(message)
        print(questions, '\n')
        qas: Dict[str, Answer] = {}
        for question in questions:
            print('[ChatSystem] Running QuestionAnswerAgent on question...')
            answer = self._qa_agent.debug_run(question, self._integrations)
            print('[ChatSystem] Answer received...')
            print(answer, '\n')
            qas[question] = answer
        print('[ChatSystem] Generating response...')
        response = self._respond_using_qas(message, qas)
        print(response, '\n')
        return response
    
    def _generate_questions_from_message(self, message: str) -> str:
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=GENERATE_QUESTIONS_SYSTEM_MESSAGE
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=message
        )
        prompt = ChatPrompt([system_message, user_message])
        llm_response = self._gpt_4.predict(prompt)
        try:
            questions = _parse_llm_response_for_questions(llm_response)
            return questions
        except ValueError:
            # Try again one more time with a scolding message.
            assistant_message = ChatPromptMessage(
                role=ChatPromptMessageRole.ASSISTANT.value,
                content=llm_response,
            )
            user_message_scold = ChatPromptMessage(
                role=ChatPromptMessageRole.USER.value,
                content='You didn\'t follow the format of the examples. Try again.',
            )
            prompt = ChatPrompt([system_message, user_message,
                                 assistant_message, user_message_scold])
            llm_response = self._gpt_4.predict(prompt)
            try:
                questions = _parse_llm_response_for_questions(llm_response)
                return questions
            except ValueError:
                return []

    def _respond_using_qas(self, message: str, qas: Dict[str, Answer]) -> str:
        if qas:
            formatted_qas = '\n\n'.join(
                [f'Question: {question}\nAnswer: {answer.content}'
                 for question, answer in qas.items()])
            system_message_content = RESPONSE_SYSTEM_MESSAGE_WITH_QAS.format(
                formatted_qas=formatted_qas
            )
        else:
            system_message_content = RESPONSE_SYSTEM_MESSAGE_WITHOUT_QAS
        if self._count_tokens(system_message_content) > MAX_TOKENS:
            return 'I received context that was too long to respond to.'
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=system_message_content
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=message
        )
        prompt = ChatPrompt([system_message, user_message])
        response = self._chat_gpt.predict(prompt)
        return response
    
    def _count_tokens(self, text: str) -> int:
        tokens = self._chat_encoding.encode(text)
        return len(tokens)

def _parse_llm_response_for_questions(llm_response: str) -> List[str]:
    try:
        matches = re.findall(r'{([^}]+)', llm_response)
        questions = list(matches)    
        return questions
    except:
        raise ValueError('llm_response is not in the correct format.') 
