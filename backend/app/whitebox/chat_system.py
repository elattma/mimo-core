from dataclasses import dataclass
from typing import Dict, List

from app.graph.blocks import ChunkFilter, PredicateFilter, QueryFilter
from app.graph.db import GraphDB
from app.mrkl.mrkl_agent import MRKLAgent
from app.mrkl.open_ai import OpenAIChat, OpenAIText
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)
from app.mrkl.tool import Tool, Toolkit
from app.util.open_ai import OpenAIClient
from app.util.vectordb import Pinecone, RowType
from neo4j import Record

response_tool_SYSTEM_MESSAGE = ChatPromptMessage(
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
        self._contexts: Dict[str, Context] = {} # TODO: fix
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
              'Input should be a question about part of the message that needs more context. '
              'Output will be a response about whether the context was or was not found.'
            ),
            func=self._context_agent.run
        )

        response_tool = Tool(
            name='Response',
            # TODO: Add history to the prompt somehow 🗺 ◻️
            description=(
              'Used to produce a response to the user\'s message. '
              'Input should be the message and any context needed to respond to the message. ' 
              'Output will be a response to the message.'
            ),
            func=self._response_tool_func
        )

        toolkit = Toolkit([
            context_agent_tool,
            response_tool
        ])

        # TODO: add prefix, suffix, etc. to improve prompt
        prompt_template = MRKLAgent.create_text_prompt_template(
            toolkit,
            prefix=(
                'Pretend you are an intelligent chat system and you are '
                'chatting with a user. If the user does not provide enough '
                'context in their message for you to produce a reasonable ' # reasonable ?
                'response, you should search for more context before '
                'responding.\n'
                'You have access to the following tools:'
            ),
            suffix=(
                'Remember to use your Context tool as many times as you need '
                'to understand the user\'s message. Once you are ready, use '
                'the Response tool to respond to the user\'s message. Begin!'
            )

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
              'Input should be the idea. ' # MAYBE CHANGE TO 'The idea you want to know more about' or something similar
              'Output will be a message about whether relevant information was found.'
            ), 
            func=self._triplet_semantics_tool_func
        )

        entity_keywords_tool = Tool(
            name='Entity Keyword Search',
            description=(
                'Used when you need more information about a keyword to answer the question. '
                ''
                ''
            ),
            func=self._entity_keyword_tool_func
        )

        toolkit = Toolkit([
            # chunk_semantics_tool,
            triplet_semantics_tool
        ])

        # TODO: add prefix, suffix, etc. to improve prompt
        prompt_template = MRKLAgent.create_text_prompt_template(
            toolkit,
            prefix=(
                'You are responsible for retrieving information that might '
                'be relevant to a query you are given.'
            ),
            suffix=(
                'Your Final Answer should state that you now know about '
                'the query.'
            )
            # You are responsible for finding data
            # You're going to be given a question
            # You must try to find context relating to the question using the tools you have access to
            # You should respond saying whether or not you were able to find context about the question
        )
        
        return MRKLAgent(
            llm,
            toolkit,
            prompt_template
        )
    
    def _response_tool_func(self, _: str) -> str:
        print('Using Response tool')
        context = '\n'.join([context.content for context in self._contexts.values()])
        print('_____________________CONTEXT_______________________')
        print(context)
        print('____________________________________________')
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
        prompt = ChatPrompt([response_tool_SYSTEM_MESSAGE, context_message, query_message])
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

        return f'I now know about {mystery}'
    
    def _triplet_semantics_tool_func(self, mystery: str) -> str:
        print('Using Triplet Semantics Tool')
        if not mystery:
            return 'no double quotes'
        # Transform as needed and return raw text
        embedding = self._openai_client.embed(mystery)
        if not embedding:
            print('failed embedding!')
            return ''
        
        nearest_neighbors = self._vector_db.query(embedding, self._owner, types=[RowType.TRIPLET], k=K)
        if not (nearest_neighbors and len(nearest_neighbors) > 0):
            print('failed nn!')
            return ''

        predicate_ids: List[str] = [neighbor.get('id', None) if neighbor else None for neighbor in nearest_neighbors]        
        query_filter = QueryFilter(
            owner=self._owner,
            predicate_filter=PredicateFilter(
                ids=predicate_ids
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(query_filter=query_filter)

        if not (results and len(results) > 0):
            print('no results found!')
            return ''
        
        context_keys = self._contexts.keys()
        for record in results:
            subject_node = record.get('s', None) if record else None
            subject_text = subject_node.get('id', None) if subject_node else None
            predicate_node =  record.get('p', None) if record else None
            predicate_id = predicate_node.get('id', None) if predicate_node else None
            predicate_text = predicate_node.get('text', None) if predicate_node else None
            object_node = record.get('o', None) if record else None
            object_text = object_node.get('id', None) if subject_node else None

            if not (subject_text and predicate_id and predicate_text and object_text):
                continue
            
            if predicate_id not in context_keys:
                self._contexts[predicate_id] = Context(content=f'{subject_text} {predicate_text} {object_text}')

        return f'I now know about {mystery}'
    
    def _entity_keyword_tool_func(self, mystery: str) -> str:
        pass