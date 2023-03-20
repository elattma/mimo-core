from dataclasses import dataclass
from typing import Dict, List

from app.client._neo4j import ChunkFilter, Neo4j, PredicateFilter, QueryFilter
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone, RowType
from app.mrkl.llm import LLM
from app.mrkl.mrkl_agent import MRKLAgent
from app.mrkl.prompt import TextPromptTemplate
from app.mrkl.tool import Tool, Toolkit
from neo4j import Record

K = 2
PREFIX = (
    'Pretend you are ContextGPT. You are responsible for finding context '
    'that is related to a query. You have access to the following tools:'
)
FORMATTING_INSTRUCTIONS = (
    'Use the following format:\n'
    'Query: the query you must find context about\n'
    'Thought: you should always think about what action to take next\n'
    'Action: the action to take, should be one of [{tool_names}]\n'
    'Action Input: the input to the action\n'
    'Observation: the result of the action\n'
    '... (this Thought/Action/Action Input/Observation pattern can repeat '
    'N times)\n'
    'Final Output: I now have all context relevant to the query'
)
SUFFIX = (
    'Remember to choose the most appropriate tool based on the query. '
    'Begin!'
)
SCRATCHPAD_START = '''Query: {query}\nThought:{scratchpad}'''


@dataclass
class Context:
    content: str


class ContextAgent(MRKLAgent):
    def __init__(
        self,
        llm: LLM,
        owner: str,
        graph_db: Neo4j,
        vector_db: Pinecone,
        openai_client: OpenAI
    ) -> None:
        self._owner = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAI = openai_client
        self._contexts: Dict[str, Context] = {}
        toolkit = self._create_toolkit()
        prompt_template = MRKLAgent.create_text_prompt_template(
            toolkit=toolkit,
            prefix=PREFIX,
            format_instructions=FORMATTING_INSTRUCTIONS,
            suffix=SUFFIX,
            scratchpad_start=SCRATCHPAD_START
        )
        super().__init__(
            llm=llm,
            toolkit=toolkit,
            prompt_template=prompt_template
        )

    @property
    def _final_answer_pattern(self) -> str:
        return 'Final Output:'

    def run(self, query: str) -> str:
        super().run(query)
        return '\n'.join(
            [context.content for context in self._contexts.values()]
        )

    def _prepare_for_new_lifecycle(self) -> None:
        self._steps = []
        self._contexts = {}

    def _create_toolkit(self) -> Toolkit:
        chunk_semantics_tool = Tool(
            name='Chunk Semantic Search',
            description=(
                'Used to find broad context that is related to the query. '
                'The input should be a single word or phrase. '
                'The output will be message from the tool indicating that '
                'context was found. '
            ),
            func=self._chunk_semantics
        )

        triplet_semantics_tool = Tool(
            name='Triplet Semantic Search',
            description=(
                'Used to find specific context that is related to the query. '
                'The input should be a single word or phrase. '
                'The output will be message from the tool indicating that '
                'context was found. '
            ),
            func=self._triplet_semantics
        )

        entity_keyword_tool = Tool(
            name='Entity Keyword Search',
            description=(
            ),
            func=self._entity_keyword
        )

        return Toolkit(
            tools=[
                chunk_semantics_tool,
                triplet_semantics_tool,
                # entity_keyword_tool
            ]
        )

    def _chunk_semantics(self, mystery: str) -> str:
        print('Using Chunk Semantics Tool')
        if not mystery:
            return 'no double quotes'

        embedding = self._openai_client.embed(mystery)
        if not embedding:
            print('failed embedding!')
            return ''

        nearest_neighbors = self._vector_db.query(
            embedding, self._owner, types=[RowType.CHUNK], k=K)
        if not (nearest_neighbors and len(nearest_neighbors) > 0):
            print('failed nn!')
            return ''

        chunk_ids = [neighbor.get(
            'id', None) if neighbor else None for neighbor in nearest_neighbors]
        query_filter = QueryFilter(
            owner=self._owner,
            chunk_filter=ChunkFilter(
                ids=chunk_ids
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(
            query_filter=query_filter)

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

        return f'I now have context about {mystery}'

    def _triplet_semantics(self, mystery: str) -> str:
        print('Using Triplet Semantics Tool')
        if not mystery:
            return 'no double quotes'

        embedding = self._openai_client.embed(mystery)
        if not embedding:
            print('failed embedding!')
            return ''

        nearest_neighbors = self._vector_db.query(
            embedding, self._owner, types=[RowType.TRIPLET], k=K)
        if not (nearest_neighbors and len(nearest_neighbors) > 0):
            print('failed nn!')
            return ''

        predicate_ids: List[str] = [neighbor.get(
            'id', None) if neighbor else None for neighbor in nearest_neighbors]
        query_filter = QueryFilter(
            owner=self._owner,
            predicate_filter=PredicateFilter(
                ids=predicate_ids
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(
            query_filter=query_filter)

        if not (results and len(results) > 0):
            print('no results found!')
            return ''

        context_keys = self._contexts.keys()
        for record in results:
            subject_node = record.get('s', None) if record else None
            subject_text = subject_node.get(
                'id', None) if subject_node else None
            predicate_node = record.get('p', None) if record else None
            predicate_id = predicate_node.get(
                'id', None) if predicate_node else None
            predicate_text = predicate_node.get(
                'text', None) if predicate_node else None
            object_node = record.get('o', None) if record else None
            object_text = object_node.get('id', None) if subject_node else None

            if not (subject_text and predicate_id and predicate_text and object_text):
                continue

            if predicate_id not in context_keys:
                self._contexts[predicate_id] = Context(
                    content=f'{subject_text} {predicate_text} {object_text}')

        return f'I now have context about {mystery}'

    def _entity_keyword(self, mystery: str) -> str:
        ...
