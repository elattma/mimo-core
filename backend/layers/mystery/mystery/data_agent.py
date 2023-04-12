import json
import re
from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict, List, Set

from external.openai_ import OpenAI
from graph.blocks import MemberBlock, entity
from graph.neo4j_ import (BlockFilter, ContentMatch, Document, DocumentFilter,
                          Limit, NameFilter, Neo4j, QueryFilter)
from graph.pinecone_ import Filter as VectorFilter
from graph.pinecone_ import Pinecone, RowType
from mystery.context_basket.model import ContextBasket, Request
from mystery.context_basket.weaver import BasketWeaver
from mystery.mrkl.open_ai import OpenAIChat
from mystery.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                                 ChatPromptMessageRole)
from mystery.query import (AbsoluteTimeFilter, BlocksFilter, Concepts, Count,
                           IntegrationsFilter, PageIds, PageParticipantRole,
                           PageParticipants, Query, QueryComponent,
                           RelativeTimeFilter, ReturnType, ReturnTypeValue, SearchMethod, SearchMethodValue)
from mystery.util import count_tokens

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------


DEFAULT_LIMIT = 20
'''The default limit on results for Neo4j queries.'''

SYSTEM_PROMPT = '''Pretend you are a data agent for a large company.
You have access to a specialized database that contains all of the company's data.
The database is represented as a graph, with three types of nodes: pages, blocks, and names.
A page is a high-level document from a data source, like an email from Google Mail or a customer account from Salesforce.
A block is a component of a page. For example, an email has a title block to store the subject, a body block to store the main message, and a member block to store the to, from, cc, and bcc.
A name is a person or organization that is linked to a page or block.
Below are descriptions about the different block types:

{block_descriptions}

Given a Request for information, your job is to create a well-formed Query to retrieve the requested information from the database.
The Query must be formatted in a specific way, and the values must make sense based on the Request.
All fields in the Query are optional, so you can leave any field blank if you don't know what to put there.
Below is the schema for a Query and explanations for what each field means:

{json_schema}

{component_descriptions}

Use the examples below to improve your understanding.
--------
EXAMPLE 1
Request: The subjects of my last 5 emails from Troy Wilkerson
Query: {{
 "page_participants": [
  {{
   "name": "Troy Wilkerson",
   "role": "author"
  }}
 ],
 "time_sort": {{
  "ascending": false,
 }},
 "count": 5,
 "integrations": ["email"],
 "blocks": ["title"],
 "search_method": "exact",
 "return_type": "blocks"
}}

EXAMPLE 2
Request: John Doe\'s strengths as an employee
Query: {{
 "concepts": ["John Doe\'s strengths as an employee"],
 "search_method": "relevant",
 "return_type": "blocks"
}}'''


# ----------------------------------------------------------------------------
# Data Agent
# ----------------------------------------------------------------------------


class DataAgent:
    _llm: OpenAIChat = None
    _basket_weaver: BasketWeaver = None

    def __init__(
        self,
        owner: str,
        graph_db: Neo4j,
        vector_db: Pinecone,
        openai: OpenAI
    ) -> None:
        print('[DataAgent] Initializing...')
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai: OpenAI = openai
        if not self._llm:
            self._llm = OpenAIChat(client=openai, model='gpt-4')
        if not self._basket_weaver:
            self._basket_weaver = BasketWeaver()
        block_descriptions = BlocksFilter.get_block_descriptions()
        json_schema = QueryComponent.get_json_schema()
        component_descriptions = QueryComponent.get_component_descriptions()
        self._system_prompt = SYSTEM_PROMPT.format(
            block_descriptions=block_descriptions,
            json_schema=json_schema,
            component_descriptions=component_descriptions
        )
        print('[DataAgent] Initialized.')

    def generate_context(
        self,
        request: str,
        query: Query = None,
        page_ids: List[str] = None,
        max_tokens: int = None
    ) -> ContextBasket:
        print('[DataAgent] Generating context...')
        # Generate query
        if page_ids:
            query = Query(
                components={
                    SearchMethod: SearchMethod(
                        value=SearchMethodValue.RELEVANT
                    ),
                    ReturnType: ReturnType(value=ReturnTypeValue.BLOCKS),
                    PageIds: PageIds(values=set(page_ids))
                }
            )
        if not query:
            query = self._generate_query(request)
        query.request = Request(
            encoding_name=self._llm.encoding_name,
            text=request,
            embedding=self._openai.embed(request)
        )

        # Use query to fetch documents
        documents = []
        default = False
        if SearchMethod not in query.components:
            default = True
        elif (query.components[SearchMethod].value
              == SearchMethodValue.EXACT):
            documents.extend(self._exact_context(query))
        elif (query.components[SearchMethod].value
              == SearchMethodValue.RELEVANT):
            if PageParticipants in query.components:
                documents.extend(
                    self._relevant_context_by_page_participants(query)
                )
            if not documents:
                default = True
        else:
            default = True
        if default:
            documents.extend(self._relevant_context(query))

        # Weave basket from documents
        basket = self._basket_weaver.weave_context_basket(
            query.request,
            documents
        )
        if max_tokens:
            self._basket_weaver.minify_context_basket(basket, max_tokens)
        print('[DataAgent] Context generated!')
        return basket

    def _exact_context(self, query: Query) -> List[Document]:
        print('[DataAgent] Filling basket with exact context...')
        results = self._query_graph_db(query=query)
        print('[DataAgent] Filled basket with exact context!')
        return results

    def _relevant_context(self, query: Query) -> List[Document]:
        print('[DataAgent] Filling basket with relevant context...')
        matches = self._query_vector_db(query)
        block_ids = set(matches.keys())
        results = self._query_graph_db(block_ids=block_ids)
        print('[DataAgent] Filled basket with relevant context!')
        return results

    def _relevant_context_by_page_participants(
        self,
        query: Query
    ) -> List[Document]:
        print((
            '[DataAgent] Filling basket with relevant context filtered by '
            'page participants...'
        ))
        matches = self._query_vector_db(query, k=100, threshold=0.70)
        block_ids = set(matches.keys())
        documents = self._query_graph_db(query, block_ids=block_ids)
        print((
            '[DataAgent] Filled basket with relevant context filtered by '
            'page participants!'
        ))
        return documents

    def _query_graph_db(
        self,
        query: Query = None,
        block_ids: Set[str] = None,
        page_ids: Set[str] = None
    ) -> List[Document]:
        print('[DataAgent] Querying graph database...')
        if not (query or block_ids or page_ids):
            return []
        query_filter = self._make_query_filter(
            query=query,
            block_ids=block_ids,
            page_ids=page_ids
        )
        if not query_filter:
            return []
        results = self._graph_db.get_by_filter(query_filter)
        if results is None:
            return []
        print('[DataAgent] Queried graph database!')
        return results

    def _query_vector_db(
        self,
        query: Query,
        k: int = 10,
        threshold: float = None
    ) -> Dict[str, float]:
        print('[DataAgent] Querying vector database...')
        vector_filter = self._make_vector_filter(query)
        embeddings = []
        if Concepts in query.components:
            c: Concepts = query.components[Concepts]
            for concept in c.values:
                embeddings.append(self._openai.embed(concept))
        if not embeddings:
            embeddings = [query.request.embedding]
        matches = {}
        for embedding in embeddings:
            relevant_blocks = self._vector_db.query(
                embedding,
                vector_filter,
                k=k
            )
            for block in relevant_blocks:
                if not threshold or block.score >= threshold:
                    matches[block.id] = block.score
        print('[DataAgent] Queried vector database!')
        return matches

    def _make_query_filter(
        self,
        query: Query = None,
        block_ids: Set[str] = None,
        page_ids: Set[str] = None,
    ) -> QueryFilter:
        integrations = None
        names = None
        time_range = None
        block_labels = None
        order_by = None
        limit = Limit(0, DEFAULT_LIMIT)
        regex_matches = None
        if query and query.components and query.request:
            if IntegrationsFilter in query.components:
                if_: IntegrationsFilter = query.components[IntegrationsFilter]
                integrations = if_.neo4j_integrations
            if PageParticipants in query.components:
                pp: PageParticipants = query.components[PageParticipants]
                names = pp.neo4j_names
                regex_matches = set()
                for participant in pp.values:
                    if participant.role == PageParticipantRole.UNKNOWN:
                        continue
                    member_block = MemberBlock(
                        last_updated_timestamp=None,
                        name=entity(
                            id=ContentMatch.get_entity_id_match_placeholder(),
                            value=None
                        ),
                        relation=participant.neo4j_relation
                    )
                    content_match = ContentMatch.from_dict(
                        matcher_dict=member_block.get_as_dict(),
                        label=MemberBlock._LABEL
                    )
                    regex_matches.add(content_match)
            if AbsoluteTimeFilter in query.components:
                atf: AbsoluteTimeFilter = query.components[AbsoluteTimeFilter]
                time_range = atf.neo4j_time_range
            if BlocksFilter in query.components:
                bf: BlocksFilter = query.components[BlocksFilter]
                block_labels = bf.neo4j_labels
            if RelativeTimeFilter in query.components:
                rtf: RelativeTimeFilter = query.components[RelativeTimeFilter]
                order_by = rtf.neo4j_order_by
            if Count in query.components:
                c: Count = query.components[Count]
                limit = c.neo4j_limit
            if PageIds in query.components:
                pi: PageIds = query.components[PageIds]
                page_ids = (page_ids.union(pi.values)
                            if page_ids else set(pi.values))

        document_filter = DocumentFilter(
            ids=page_ids if page_ids else None,
            integrations=integrations,
            time_range=time_range
        )
        name_filter = NameFilter(names=names)
        block_filter = BlockFilter(
            ids=block_ids if block_ids else None,
            labels=block_labels,
            time_range=time_range,
            regex_matches=regex_matches
        )

        query_filter = QueryFilter(
            owner=self._owner,
            document_filter=document_filter,
            name_filter=name_filter,
            block_filter=block_filter,
            order_by=order_by,
            limit=limit
        )
        return query_filter

    def _make_vector_filter(self, query: Query) -> VectorFilter:
        integrations = None
        min_date_day = None
        max_date_day = None
        block_labels = None
        document_id = None
        if IntegrationsFilter in query.components:
            if_: IntegrationsFilter = query.components[IntegrationsFilter]
            integrations = if_.pinecone_integrations
        if AbsoluteTimeFilter in query.components:
            atf: AbsoluteTimeFilter = query.components[AbsoluteTimeFilter]
            min_date_day = atf.pinecone_min_date_day
            max_date_day = atf.pinecone_max_date_day
        if BlocksFilter in query.components:
            bf: BlocksFilter = query.components[BlocksFilter]
            block_labels = bf.pinecone_labels
        if PageIds in query.components:
            pi: PageIds = query.components[PageIds]
            document_id = pi.values

        vector_filter = VectorFilter(
            owner=self._owner,
            type=set([RowType.BLOCK]),
            min_date_day=min_date_day,
            max_date_day=max_date_day,
            integration=integrations,
            block_label=block_labels,
            document_id=document_id
        )
        return vector_filter

    def _get_page_ids_from_results(self, results: List[Document]) -> Set[str]:
        page_ids = [document.id for document in results]
        return set(page_ids)

    def _generate_query(self, request: str) -> Query:
        print('[DataAgent] Generating query...')
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=self._system_prompt
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=request
        )
        prompt = ChatPrompt([system_message, user_message])
        llm_response = self._llm.predict(prompt)
        query = _query_from_llm_response(llm_response)
        print('[DataAgent] Generated query!')
        print(query)
        return query

    def _generate_prompt(
        self,
        request: str
    ) -> ChatPrompt:
        print('[DataAgent] Generating prompt...')
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=self._system_prompt
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=request
        )
        prompt = ChatPrompt([system_message, user_message])
        print('[DataAgent] Prompt generated!')
        return prompt

    def _context_basket_token_size(
        self,
        context_basket: ContextBasket
    ) -> int:
        token_count = 0
        for context in context_basket:
            token_count += count_tokens(context.content,
                                        self._llm.encoding_name)
        return token_count


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------


def _query_from_llm_response(llm_response: str) -> Query:
    match = re.search(r'{[\s\S]*}', llm_response, re.DOTALL)
    if match:
        stringified_json = match.group(0)
        query_json = json.loads(stringified_json)
        query = Query.from_llm_response(query_json)
        return query


def _node_get(node: Dict, property: str) -> Any:
    return node.get(property, None) if node else None


def _euclidean_distance(row1, row2):
    distance = 0.0
    for i in range(len(row1)-1):
        distance += (row1[i] - row2[i])**2
    return sqrt(distance)


@ dataclass
class Vector:
    id_: str
    embedding: List[float]
    distance = float = None


def _get_neighbors(
    query_vector: Vector,
    block_vectors: List[Vector],
    num_neighbors: int = 5
) -> List[Vector]:
    query_embedding = query_vector.embedding
    for block_vector in block_vectors:
        distance = _euclidean_distance(
            query_embedding,
            block_vector.embedding
        )
        block_vector.distance = distance
    sorted_block_vectors = sorted(block_vectors, key=lambda x: x.distance)
    return sorted_block_vectors[:num_neighbors]


# TODO: move to somewhere that makes sense
def _decorate_block_embeddings(
    _vector_db: Pinecone,
    documents: List[Document]
) -> None:
    ids: List[str] = []
    for document in documents:
        ids.extend([consists.target.id for consists in document.consists])

    embeddings = _vector_db.fetch(ids)
    block_vectors = {}
    for id_, vector in embeddings.items():
        block_vectors[id_] = vector.values

    for document in documents:
        for consists in document.consists:
            consists.target.embedding = block_vectors.get(
                consists.target.id, None)
