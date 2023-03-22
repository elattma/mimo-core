from typing import List, Dict
from functools import reduce

from tiktoken import Encoding, get_encoding
from app.client._neo4j import Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone
from app.mrkl.mrkl_agent import MRKLAgent
from app.mrkl.open_ai import OpenAIChat, OpenAIText
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)
from app.mystery.context_agent import ContextAgent, Context

MAX_TOKENS = 3000
SYSTEM_MESSAGE = '''Pretend you are now DataGPT. You know everything that GPT-4 was trained on.
Your only job is to look at an input and make a list of what you wish you knew more about.
You can learn more about a company's entire knowledge base.
The knowledge base has all data, people, or concepts that would be accessible to an employee at the company.
The examples below will show you how to think. Follow the format of the examples.
---------
EXAMPLES:
Input: Summarize all documents referring to Troy Wilkerson
Output: [{all documents referring to Troy Wilkerson}]
Input: What do people at Jefferies think about deadlines?
Output: [{people's thoughts about deadlines at Jefferies}]
Input: What was the click through rate of the most 
recent retargeting campaign? How much did it cost?
Output: [{click through rate of most recent retargeting 
campaign} {cost of most recent retargeting campaign}]
Input: What is the capital of Italy? Who was our highest 
paying customer last quarter?
Output: [{highest paying customer last quarter}].
Input: What has been the most common complaint across Intercom tickets this week?
Output: [{all Intercom tickets this week}]
Input: What's the difference between v1 of the product and v2?
Output: [{product description of v1} {product description of v2}]
Input: Write a summary of Mo's pull requests over the past month?
Output: [{Mo's pull requests over the past month}]'''

K=2
class ChatSystem:
    _gpt_4: OpenAIChat = None
    _chat_gpt: OpenAIChat = None
    _context_agent: ContextAgent = None
    _chat_encoding: Encoding = None

    def __init__(
        self,
        owner: str,
        graph_db: Neo4j,
        vector_db: Pinecone,
        openai_client: OpenAI
    ) -> None:
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAI = openai_client
        if not self._gpt_4:
            self._gpt_4 = OpenAIChat(client=openai_client, model='gpt-4')
        if not self._chat_gpt:
            self._chat_gpt = OpenAIChat(client=openai_client, model='gpt-3.5-turbo')
        if not self._context_agent:
            self._context_agent = ContextAgent(
                llm=self._gpt_4,
                owner=self._owner,
                graph_db=self._graph_db,
                vector_db=self._vector_db,
                openai_client=self._openai_client
            )
        if not self._chat_encoding:
            self._chat_encoding = get_encoding(
                self._gpt_4.encoding_name
            )

    def run(self, query: str) -> str:
        '''Produces a response to a query that is contextualized by the user's
        knowledge base.
          Args:
            query `str`: The user's message.

          Returns:
            `str`: The contextualized response to the user's message.
        '''
        # Call GPT-4 to make a plan for the context that needs to be fetched
        raw_steps: str = self._get_steps(query)
        steps: List[str] = _parse_steps(raw_steps)

        print('--------SYSTEM: STEPS--------')
        print(steps)
        print()
        # Fetch the contexts from the context agent, preserving the query they
        # provide context for
        contexts: Dict[str, Context] = {}
        for step in steps:
            contexts[step] = self._context_agent.run(step)

        # Minify each context if the total number of tokens is too large
        token_count = reduce(
            lambda total, text: total + self._count_tokens(text),
            contexts.values(),
            0
        )
        if token_count > MAX_TOKENS:
            contexts = _minify_contexts(contexts)

        prompt_context = '\n\n'.join([
            (f'Context for "{step}":\n{context}') for step, context in contexts.items()
        ])

        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=f'''Use this context to answer the user's message:
            {prompt_context}'''
        )

        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=query
        )

        prompt = ChatPrompt(
            messages=[system_message, user_message]
        )

        return self._chat_gpt.predict(prompt=prompt)
            

    def _get_steps(self, query: str) -> str:
        '''Calls GPT-4 to get the steps for the context that needs to be fetched.
          Args:
            query `str`: The user's message.

          Returns:
            `str`: The raw steps from the GPT-4 call.
        '''
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=SYSTEM_MESSAGE
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=(
                f'Input: {query}\n'
                'Output: '
            )
        )
        prompt = ChatPrompt(
            messages=[system_message, user_message]
        )
        return self._gpt_4.predict(prompt)

    def _count_tokens(self, text: str) -> int:
        '''Counts the number of tokens in a string.
          Args:
            text `str`: The string to count the tokens of.

          Returns:
            `int`: The number of tokens in the string.
        '''
        tokens = self._chat_encoding.encode(text)
        return len(tokens)


def _parse_steps(raw_steps: str) -> List[str]:
    '''Parses the raw steps from the GPT-4 call 
    into a list of steps.

      Args:
        raw_steps `str`: The raw steps from the GPT-4 call.

      Returns:
        `List[str]`: The list of steps.
    '''
    if not raw_steps.startswith('[{'):
        return []
    steps: List[str] = []
    if raw_steps:
        steps = raw_steps[2:-2].split('} {')
    return steps


def _minify_contexts(contexts: Dict[str, Context]) -> Dict[str, Context]:
    '''Produces an appropriately sized context string from a set of contexts
    whose total token count is too large.

      Args:
        contexts `Dict[str, Context]`: The contexts to minify keyed by the query
        that produced them.

      Returns:
        `Dict[str, Context]`: The minified contexts.
    '''
    ...
