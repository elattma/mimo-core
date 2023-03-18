from typing import List

from app.graph.db import GraphDB
from app.mrkl.mrkl_agent import MRKLAgent
from app.mrkl.open_ai import OpenAIChat, OpenAIText
from app.util.open_ai import OpenAIClient
from app.util.vectordb import Pinecone
from app.whitebox.context_agent import ContextAgent
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)


class ChatSystem:
    _text_llm: OpenAIText = None
    _chat_llm: OpenAIChat = None
    _context_agent: ContextAgent = None

    def __init__(
        self,
        owner: str,
        graph_db: GraphDB,
        vector_db: Pinecone,
        openai_client: OpenAIClient
    ) -> None:
        self._owner: str = owner
        self._graph_db: GraphDB = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAIClient = openai_client
        if not self._text_llm:
            self._text_llm = OpenAIText(client=openai_client)
        if not self._chat_llm:
            self._chat_llm = OpenAIChat(client=openai_client, model='gpt-4')
        if not self._context_agent:
            self._context_agent = ContextAgent(
                llm=self._text_llm,
                owner=self._owner,
                graph_db=self._graph_db,
                vector_db=self._vector_db,
                openai_client=self._openai_client
            )

    def run(self, query: str) -> str:
        '''Produces a response to a query that is contextualized by the user's
        knowledge base.
          Args:
            query `str`: The user's message.

          Returns:
            `str`: The contextualized response to the user's message.
        '''
        # 1. GPT-4 call to create a plan for the context that needs to be
        # fetched
        raw_steps: str = self._get_steps(query)
        print("--------RAW STEPS--------")
        print(raw_steps)
        steps: List[str] = _parse_steps(raw_steps)
        print("--------STEPS--------")
        print(steps)
        # 2. For each step, call the ContextAgent to get context
        # for step in steps:
        #     print(self._context_agent.run(step))
        # 3. Call gpt-3.5-turbo with a prompt that includes the context

    def _get_steps(self, query: str) -> str:
        '''Calls GPT-4 to get the steps for the context that needs to be fetched.
          Args:
            query `str`: The user's message.

          Returns:
            `str`: The raw steps from the GPT-4 call.
        '''
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=(
                'You are ChatGPT. Respond to the user\'s input.'
                'Pretend you are now PlanGPT. Your job consists of two '
                'steps.\n1. Determine if you need more context to respond '
                'to the input.\n2. If you need more context, list the '
                'concepts that are not precise and clear.\n'
                'Follow the format in the examples below.\n'
                'If you do not need more context, say "Done".\n'
                '--------\n'
                'EXAMPLES:\n'
                'Input: Summarize all documents referring to Troy Wilkerson\n'
                'Output: [{all documents referring to Troy Wilkerson}]\n\n'
                'Input: What do people at Jefferies think about deadlines?\n'
                'Output: [{people\'s opinions about deadlines at Jefferies}]'
                '\n\nInput: How effective was the most recent retargeting '
                'campaign? How much did it cost?\n'
                'Output: [{efficacy of most recent retargeting campaign} '
                '{cost of most recent retargeting campaign}]\n'
                'Input: What is the capital of Italy? Who was our highest '
                'paying customer last quarter?\n'
                'Output: [{highest paying customer last quarter}]\n'
            )
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
        return self._chat_llm.predict(prompt)


def _parse_steps(raw_steps: str) -> List[str]:
    '''Parses the raw steps from the GPT-4 call into a list of steps.

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
