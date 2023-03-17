from dataclasses import dataclass
from typing import Dict, List

from app.graph.blocks import ChunkFilter, QueryFilter
from app.graph.db import GraphDB
from app.mrkl.mrkl_agent import MRKLAgent
from app.mrkl.open_ai import OpenAIChat, OpenAIText
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)
from app.mrkl.tool import Tool, Toolkit
from app.util.open_ai import OpenAIClient
from app.util.vectordb import Pinecone, RowType
from neo4j import Record

CHAT_TOOL_SYSTEM_MESSAGE = ChatPromptMessage(
    role=ChatPromptMessageRole.SYSTEM.value,
    content='Respond to the message from the user using the provided context.'
)

K = 5

@dataclass
class Context:
    content: str

class ChatSystem:
    _text_llm: OpenAIText = None
    _chat_llm: OpenAIChat = None
    _orchestrator_agent: MRKLAgent = None
    _context_agent: MRKLAgent = None

    def __init__(self, owner: str, graph_db: GraphDB, vector_db: Pinecone, openai_client: OpenAIClient):
        self._owner = owner
        self._graph_db = graph_db
        self._vector_db = vector_db
        self._openai_client = openai_client
        self._contexts: Dict[str, Context] = {}
        self._query: str = None
        if not self._text_llm:
            self._text_llm = OpenAIText(client=openai_client)
        if not self._chat_llm:
            self._chat_llm = OpenAIChat(client=openai_client)
        if not self._context_agent:
            self._context_agent = self._create_context_agent()
        if not self._orchestrator_agent:
            self._orchestrator_agent = self._create_orchestrator_agent()

    def run(self, query: str) -> str:
        self._query = query
        return self._orchestrator_agent.run(query)
    
    def _create_orchestrator_agent(self) -> MRKLAgent:
        llm = self._text_llm

        context_agent_tool = Tool(
            name='Context',
            description=(
              'Used when more context is needed to respond to the user\'s '
              'message. '
              'Input should be the part of the message that needs more context. '
              'Output will be the context.'
            ),
            func=self._context_agent.run
        )

        chat_tool = Tool(
            name='Chat',
            # TODO: Add history to the prompt somehow 🗺 ◻️
            description=(
              'Used to produce an answer to the user\'s message. '
              'Input should be the message and any context needed to respond to the message. ' 
              'Output will be a response to the message.'
            ),
            func=self._chat_tool_func
        )

        toolkit = Toolkit([
            context_agent_tool,
            chat_tool
        ])

        # TODO: add prefix, suffix, etc. to improve prompt
        prompt_template = MRKLAgent.create_text_prompt_template(
            toolkit,
            prefix=(
                'Your job is to produce a contextualized response to the '
                'user\'s message.\n'
                'Your order of actions should be: 1. Determine if you have '
                'enough context to respond to the message 2. If you need '
                'more context, use the Context tool as many times as needed '
                '3. Use the Chat tool to produce a response to the user\'s'
                ' message.\n'
                'You have access to the following tools:'
            ),
            suffix='Remember your order of actions. Begin!'

        )

        return MRKLAgent(
            llm,
            toolkit,
            prompt_template
        )
    
    def _create_context_agent(self) -> MRKLAgent:
        llm = self._text_llm

        chunk_semantics_tool = Tool(
            name='Chunk Semantic Search',
            description=(
              'Used to get entire chunks of text. '
              'Input should be input text. '
              'Output will be a message about whether relevant information was found.'
            ), 
            func=self._chunk_semantics_tool_func
        )

        triplet_semantics_tool = Tool(
            name='Triplet Semantic Search',
            description=(
              'Used to get more information about an idea and the idea\'s relationships. '
              'Input should be the idea. ' # MAYBE CHANGE TO "The idea you want to know more about" or something similar
              'Output will be a message about whether relevant information was found.'
            ), 
            func=self._triplet_semantics_tool_func
        )

        entity_keywords_tool = Tool(
            name='Entity Keyword Search',
            description=(
                'Used to get information about a keyword. '
                ''
                ''
            ),
            func=self._entity_keyword_tool_func
        )

        toolkit = Toolkit([
            chunk_semantics_tool,
            # triplet_semantics_tool
        ])

        # TODO: add prefix, suffix, etc. to improve prompt
        prompt_template = MRKLAgent.create_text_prompt_template(
            toolkit
        )
        
        return MRKLAgent(
            llm,
            toolkit,
            prompt_template
        )
    
    def _chat_tool_func(self, _: str) -> str:
        print('Using Chat tool')
        context = '\n'.join([context.content for context in self._contexts.values()])
        context_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=(
              '--------------------\n'
              'Here is context to use for your response.\n'
              f'{context}'
              '--------------------\n'
            )
        )
        query_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=self._query
        )
        prompt = ChatPrompt([CHAT_TOOL_SYSTEM_MESSAGE, context_message, query_message])
        return self._chat_llm.predict(prompt)

    def _chunk_semantics_tool_func(self, mystery: str) -> str:
        print('Using Chunk Semantics Tool')
        if not mystery:
            return 'no double quotes'
        # Transform as needed and return raw text
        embedding = self._openai_client.embed(mystery)
        if not embedding:
            print('failed embedding!')
            return ''
        
        nearest_neighbors = self._vector_db.query(embedding, self._owner, types=[RowType.CHUNK], k=K)
        if not (nearest_neighbors and len(nearest_neighbors) > 0):
            print('failed nn!')
            return ''

        chunk_ids = [neighbor.get('id', None) if neighbor else None for neighbor in nearest_neighbors]        
        query_filter = QueryFilter(
            owner=self._owner,
            chunk_filter=ChunkFilter(
                ids=chunk_ids
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(query_filter=query_filter)

        if not (results and len(results) > 0):
            print('no results found!')
            return ''
        
        context_keys = self._contexts.keys()
        for record in results:
            chunk = record.get('c', None) if record else None
            chunk_id = chunk.get('id', None) if chunk else None
            chunk_content = chunk.get('content', None) if chunk else None
            if not (chunk_id and chunk_content):
                continue
            
            if chunk_id not in context_keys:
                self._contexts[chunk_id] = Context(content=chunk_content)

        return f'You now have the context for {mystery}'
    
    def _triplet_semantics_tool_func(self, mystery: str) -> str:
        pass
    