import datetime
import json
import re
from abc import ABC, abstractstaticmethod
from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from typing import Any, Dict, List, Set, Tuple, Type, Union

from external.openai_ import OpenAI
from graph.neo4j_ import (BlockFilter, Document, DocumentFilter, Limit,
                          NameFilter, Neo4j, OrderBy, OrderDirection,
                          QueryFilter)
from graph.pinecone_ import Filter as VectorFilter
from graph.pinecone_ import Pinecone, RowType
from mystery.mrkl.open_ai import OpenAIChat
from mystery.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                                 ChatPromptMessageRole)
from mystery.util import count_tokens

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

SYSTEM_PROMPT = '''Pretend you are a data agent for a large company.
You have access to a specialized database that contains all of the company's data.
The database is represented as a graph, with three types of nodes: pages, blocks, and names.
A page is a high-level document from a data source, like an email from Google Mail or a customer account from Salesforce.
A block is a component of a page. For example, an email has a title block to store the subject, a body block to store the main message, and a members block to store the to, from, cc, and bcc.
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
 "page_participants": ["Troy Wilkerson"],
 "time_sort": {{
  "ascending": false,
  "count": 5
 }},
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
# Query
# ----------------------------------------------------------------------------

class QueryComponent(ABC):
    '''An abstract class for a component of a Query.'''
    @abstractstaticmethod
    def from_llm_response(s: str) -> 'QueryComponent':
        '''Converts a string generated by an LLM to a QueryComponent.'''
        raise NotImplementedError

    @abstractstaticmethod
    def description_for_prompt() -> str:
        '''Returns a description of the component for use in a prompt.'''
        raise NotImplementedError
    
    @abstractstaticmethod
    def json_for_prompt() -> str:
        '''Returns how the component should be represented in the prompt's
        sample JSON.'''
        raise NotImplementedError
    
    @staticmethod
    def get_component_descriptions() -> str:
        '''Returns a description of all components for use in a prompt.'''
        component_descriptions = [c.description_for_prompt()
                                  for c in QueryComponent.get_components_list()]
        return '\n'.join(component_descriptions)
    
    @staticmethod
    def get_json_schema() -> str:
        '''Returns a JSON schema for all components for use in a prompt.'''
        json_parts = [c.json_for_prompt()
                      for c in QueryComponent.get_components_list()]
        return '{\n' + ',\n'.join(json_parts) + '\n}'

    @staticmethod
    def get_component_from_json_key(key: str) -> 'QueryComponent':
        lookup = {
            'concepts': Concepts,
            'page_participants': PageParticipants,
            'time_frame': AbsoluteTimeFilter,
            'time_sort': RelativeTimeFilter,
            'sources': IntegrationsFilter,
            'blocks': BlocksFilter,
            'search_method': SearchMethod,
            'return_type': ReturnType,
        }
        if key not in lookup:
            raise ValueError(f'Invalid key: {key}')
        return lookup[key]
    
    @staticmethod
    def get_components_list() -> List['QueryComponent']:
        '''Returns a list of all components as QueryComponent objects.'''
        return [
            Concepts,
            PageParticipants,
            AbsoluteTimeFilter,
            RelativeTimeFilter,
            IntegrationsFilter,
            BlocksFilter,
            SearchMethod,
            ReturnType,
        ]

@dataclass
class Concepts(QueryComponent):
    '''Suggests semantically important concepts from the request.'''
    values: List[str]

    @staticmethod
    def from_llm_response(llm_response: List[str]) -> 'Concepts':
        if not Concepts._validate_llm_response(llm_response):
            print('Failed to create Concepts from LLM response:',
                  llm_response)
            return None
        return Concepts(llm_response)
    
    @staticmethod
    def description_for_prompt() -> str:
        return ('concepts: A list of independent concepts that are '
                'semantically important. These concepts are extracted from '
                'the Request. They should capture whole ideas, not just '
                'individual words. For example, if the request is "Documents '
                'about the role of AI in the workplace", the concepts should '
                'be ["role of AI in the workplace"], not ["role", "AI", '
                '"workplace"].')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "concepts": string[]'
    
    @staticmethod
    def _validate_llm_response(llm_response: List[str]) -> bool:
        return bool(llm_response)
    
@dataclass
class PageParticipants(QueryComponent):
    '''Enforces that only results linked to these names are considered.'''
    values: List[str]

    @staticmethod
    def from_llm_response(llm_response: List[str]) -> 'PageParticipants':
        if not PageParticipants._validate_llm_response(llm_response):
            print('Failed to create PageParticipants from LLM response:',
                  llm_response)
            return None
        return PageParticipants(llm_response)
    
    @staticmethod
    def description_for_prompt() -> str:
        return ('page_participants: A list of names, e.g. people or '
                'organizations, that are linked to the creation of the '
                'information you are searching for.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "page_participants": string[]'
    
    @property
    def neo4j_names(self) -> Set[str]:
        '''Returns a set of names for use in Neo4j.'''
        return set(self.values)

    @staticmethod
    def _validate_llm_response(llm_response: List[str]) -> bool:
        return bool(llm_response)

@dataclass
class AbsoluteTimeFilter(QueryComponent):
    '''Enforces that only results within this time frame are considered. e.g.
    "between 2020 and 2022", "in the last 5 days"'''
    start: int = None
    end: int = None

    @staticmethod
    def from_llm_response(
        llm_response: Dict[str, str]) -> 'AbsoluteTimeFilter':
        # llm_response should be a dictionary with two keys: 'start' and
        # 'end'. Each value should be a string in the format 'YYYY-MM-DD'.
        start = llm_response.get('start', None)
        end = llm_response.get('end', None)
        start_valid = AbsoluteTimeFilter._validate_date(start)
        end_valid = AbsoluteTimeFilter._validate_date(end)
        if not (start_valid or end_valid):
            print('Failed to create AbsoluteTimeFilter from LLM response:',
                  llm_response)
            return None
        start = _format_date(llm_response['start']) if start_valid else None
        end = _format_date(llm_response['end']) if end_valid else None
        return AbsoluteTimeFilter(start=start, end=end)

    @staticmethod
    def description_for_prompt() -> str:
        current_date = _get_today_date()
        return ('time_frame: Include time_frame if the Request implies that '
                'the requested information was created within a specific '
                f'time frame. It is currently {current_date}.')
    
    @staticmethod
    def json_for_prompt() -> str:
        return (' "time_frame": {\n'
                '  "start": string,\n'
                '  "end": string\n'
                ' }')
    
    @property
    def neo4j_time_range(self) -> Tuple[int, int]:
        '''Returns a range of timestamps for use in Neo4j.'''
        start_timestamp = (_date_day_to_timestamp(self.start)
                           if self.start else 0)
        end_timestamp = (_date_day_to_timestamp(self.end)
                         if self.end else _get_today_timestamp())
        return (start_timestamp, end_timestamp)
    
    @property
    def pinecone_min_date_day(self) -> int:
        '''Returns the minimum date day for use in Pinecone.'''
        return self.start if self.start else 0
    
    @property
    def pinecone_max_date_day(self) -> int:
        '''Returns the maximum date day for use in Pinecone.'''
        return self.end if self.end else _get_today_date_day()

    @staticmethod
    def _validate_date(maybe_date: str) -> bool:
        try:
            return re.match(r'\d{4}-\d{2}-\d{2}', str(maybe_date))
        except:
            return False

@dataclass
class RelativeTimeFilter(QueryComponent):
    '''Enforces relative ordering of results based on time. e.g. 
    "most recent", "the five oldest"'''
    ascending: bool
    count: int

    @staticmethod
    def from_llm_response(
        llm_response: Dict[str, Union[bool, int]]) -> 'RelativeTimeFilter':
        # llm_response should be a dictionary with two keys: 'ascending' and
        # 'count'. The value of 'ascending' should be a boolean and the value
        # of 'count' should be an integer.
        if not RelativeTimeFilter._validate_llm_response(llm_response):
            print('Failed to create RelativeTimeFilter from LLM response:',
                  llm_response)
            return None
        ascending = llm_response['ascending']
        count = llm_response['count']
        return RelativeTimeFilter(ascending, count)
    
    @staticmethod
    def description_for_prompt() -> str:
        return ('time_sort: Inlude a time_sort if the Request is requesting '
                'information based on a relative ordering of time.')

    @staticmethod
    def json_for_prompt() -> str:
        return (' "time_sort": {\n'
                '  "ascending": boolean,\n'
                '  "count": integer\n'
                ' }')
    
    @property
    def neo4j_order_by(self) -> OrderBy:
        '''Returns an OrderBy object for use in Neo4j.'''
        direction = (OrderDirection.ASC
                     if self.ascending else OrderDirection.DESC)
        return OrderBy(direction, 'block', 'last_updated_timestamp')
    
    @property
    def neo4j_limit(self) -> Limit:
        '''Returns a Limit object for use in Neo4j.'''
        return Limit(0, self.count)
    
    @staticmethod
    def _validate_llm_response(
        llm_response: Dict[str, Union[bool, int]]) -> bool:
        if not (llm_response and 'ascending' in llm_response and
                'count' in llm_response):
            return False
        ascending = llm_response['ascending']
        count = llm_response['count']
        if not (isinstance(ascending, bool) and isinstance(count, int)
                and count > 0):
            return False
        return True

class Integration(Enum):
    CRM = 'crm'
    CUSTOMER_SUPPORT = 'customer_support'
    DOCUMENTS = 'documents'
    EMAIL = 'email'

@dataclass
class IntegrationsFilter(QueryComponent):
    '''Enforces that only results from these integrations are considered. e.g.
    'gmail', 'zendesk' '''
    integrations: List[Integration]

    @staticmethod
    def from_llm_response(llm_response: List[str]) -> 'IntegrationsFilter':
        if not llm_response:
            return None
        try:
            integrations = [Integration(integration) for integration in
                            llm_response]
        except ValueError:
            print('Failed to create IntegrationsFilter from LLM response:',
                  llm_response)
            return None
        return IntegrationsFilter(integrations)
    
    @staticmethod
    def description_for_prompt() -> str:
        data_sources = ', '.join([f'"{integration.value}"' for integration in
                                  Integration])
        data_sources = f'[{data_sources}]'
        return ('sources: Identify any data sources that are referenced in '
                'the Request. The possible data sources are: '
                f'{data_sources}.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "sources": string[]'
    
    @property
    def neo4j_integrations(self) -> Set[str]:
        '''Returns a list of integration names for use in Neo4j.'''
        return set([_integration_name(integration)
                    for integration in self.integrations])
    
    @property
    def pinecone_integrations(self) -> Set[str]:
        '''Returns a list of integration names for use in Pinecone.'''
        return set([_integration_name(integration)
                    for integration in self.integrations])

class Block(Enum):
    BODY = 'body'
    COMMENT = 'comment'
    CONTACT = 'contact'
    DEAL = 'deal'
    MEMBERS = 'members'
    SUMMARY = 'summary'
    TITLE = 'title'

@dataclass
class BlocksFilter(QueryComponent):
    '''Enforces that only results from these blocks are considered. e.g.
    "title contains", "summarize"'''
    blocks: List[Block]
    block_ids: List[str] = None

    @staticmethod
    def from_llm_response(llm_response: List[str]) -> 'BlocksFilter':
        if not llm_response:
            return None
        try:
            blocks = [Block(block) for block in llm_response]
        except ValueError:
            print('Failed to create BlocksFilter from LLM response:',
                  llm_response)
            return None
        return BlocksFilter(blocks)
    
    @staticmethod
    def description_for_prompt() -> str:
        blocks = ', '.join([f'"{block.value}"' for block in Block])
        blocks = f'[{blocks}]'
        return ('blocks: Include this field only if the information relevant '
                'to the Request is guaranteed to be contained within a '
                'specific block or set of blocks. '
                f'The possible blocks are: {blocks}.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "blocks": string[]'
    
    @staticmethod
    def get_block_descriptions() -> str:
        return ('"body": The body of the page, e.g. the text in a '
                'Microsoft Word document.\n'
                '"comment": A comment on the page, e.g. a comment on a Jira '
                'ticket.\n'
                '"contact": A contact associated with an account in a CRM.\n'
                '"deal": A deal associated with an account in a CRM.\n'
                '"members": A list of members associated with the page, e.g. '
                'the author, recipients, etc.\n'
                '"summary": A summary of the page.\n'
                '"title": The title of the page.')
    
    @property
    def neo4j_labels(self) -> Set[str]:
        '''Returns a list of block labels for use in Neo4j.'''
        return set([block.value for block in self.blocks])
    
    @property
    def pinecone_labels(self) -> Set[str]:
        '''Returns a list of block labels for use in Pinecone.'''
        return set([block.value for block in self.blocks])

class SearchMethodValue(Enum):
    RELEVANT = 'relevant'
    EXACT = 'exact'

@dataclass
class SearchMethod(QueryComponent):
    '''Enforces the method by which results are returned.\n
    Examples:\n
    "all emails from Troy" => "exact"\n
    "emails from Troy related to the budget" => "relevant"'''
    value: SearchMethodValue

    @staticmethod
    def from_llm_response(llm_response: str) -> 'SearchMethod':
        try:
            value = SearchMethodValue(llm_response)
        except ValueError:
            print('Failed to create SearchMethod from LLM response:',
                  llm_response)
            return None
        return SearchMethod(value)
    
    @staticmethod
    def description_for_prompt() -> str:
        return ('search_method: Determine whether the Request is looking '
                'for exact information or the most relevant information.')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "search_method": "exact" OR "relevant"'

class ReturnTypeValue(Enum):
    PAGES = 'pages'
    BLOCKS = 'blocks'

@dataclass
class ReturnType(QueryComponent):
    value: str

    @staticmethod
    def from_llm_response(llm_response: str) -> 'ReturnType':
        try:
            value = ReturnTypeValue(llm_response)
        except ValueError:
            print('Failed to create ReturnType from LLM response:',
                  llm_response)
            return None
        return ReturnType(value)
    
    @staticmethod
    def description_for_prompt() -> str:
        return ('return_type: If the Request is explicitly seeking an '
                'entire page, select "pages". Otherwise, select "blocks".')

    @staticmethod
    def json_for_prompt() -> str:
        return ' "return_type": "pages" OR "blocks"'

@dataclass
class Query:
    components: Dict[Type[QueryComponent], QueryComponent] = (
        field(default_factory=dict))
    question: str = None
    
    @staticmethod
    def from_llm_response(llm_response: Dict[str, Any]) -> 'Query':
        components = {}
        for key, value in llm_response.items():
            try:
                component_class = QueryComponent.get_component_from_json_key(
                    key)
            except ValueError:
                print(f'LLM produced invalid query component: {key}')
                continue
            component = component_class.from_llm_response(value)
            if component:
                components[component_class] = component
        return Query(components)
    
# ----------------------------------------------------------------------------
# Context
# ----------------------------------------------------------------------------

@dataclass
class Source:
    page_id: str
    integration: str

@dataclass
class Context:
    content: str 
    source: Source

@dataclass
class ContextBasket:
    contexts: List[Context] = field(default_factory=list) 

    def append(self, context: Context) -> None:
        self.contexts.append(context)

    def extend(self, contexts: List[Context]) -> None:
        self.contexts.extend(contexts)

    def __iter__(self):
        return iter(self.contexts)

# ----------------------------------------------------------------------------
# Data Agent
# ----------------------------------------------------------------------------

class DataAgent(ABC):
    '''The data agent abstract class.'''
    _llm: OpenAIChat = None

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
            self, question: str, query: Query = None) -> ContextBasket:
        print('[DataAgent] Generating context...')
        if not query:
            prompt = self._generate_prompt(question)
            print('[DataAgent] Generating query string from LLM...')
            llm_response = self._llm.predict(prompt)
            print('[DataAgent] Generated query string from LLM!')
            print(llm_response)
            query = _parse_llm_response_for_query(llm_response)
            query.question = question
        if (SearchMethod in query.components and
            query.components[SearchMethod].value == SearchMethodValue.EXACT):
            context_basket = self._fetch_exact_context(query)
        elif (SearchMethod in query.components and
                query.components[SearchMethod].value ==
                SearchMethodValue.RELEVANT):
            if (PageParticipants in query.components
                and query.components[PageParticipants]):
                context_basket = self._fetch_relevant_context_with_names(query)
            else:
                context_basket = self._fetch_relevant_context_without_names(query)
        else:
            print('[DataAgent] (Warning) Invalid SearchMethod')
            context_basket = self._fetch_relevant_context_without_names(query)
        if len(context_basket.contexts) < 1:
            context_basket = self._fetch_relevant_context_without_names(query)
        print('[DataAgent] Context generated!')
        for context in context_basket.contexts:
            print(context.content)
        return context_basket
        
    def _generate_prompt(
        self,
        question: str
    ) -> ChatPrompt:
        print('[DataAgent] Generating prompt...')
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=self._system_prompt
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=question
        )
        prompt = ChatPrompt([system_message, user_message])
        print('[DataAgent] Prompt generated!')
        return prompt
    
    def _fetch_relevant_context_without_names(self, query: Query) -> ContextBasket:
        print('[DataAgent] Fetching relevant context without names...')
        context_basket = ContextBasket()
        question_embedding = self._openai.embed(query.question)
        vector_filter = self._generate_vector_filter(query)
        self._fill_basket_from_embedding(context_basket, vector_filter,
                                         question_embedding)
        print('[DataAgent] Fetched relevant context without names!')
        return context_basket
    
    def _fetch_relevant_context_with_names(
            self, query: Query) -> ContextBasket:
        print('[DataAgent] Fetching relevant context with names...')
        results = self._query_neo4j(query)
        block_ids = []
        if results:
            for record in results:
                block_node = _node_get(record, 'block')
                id_ = _node_get(block_node, 'id')
                if id_:
                    block_ids.append(id_)
        block_embeddings = self._vector_db.fetch(block_ids)
        block_vectors = []
        if block_embeddings:
            block_vectors = [Vector(id_, vector.values)
                            for id_, vector in block_embeddings.items()]
        question_embedding = self._openai.embed(query.question)
        question_vector = Vector('', question_embedding)
        nearest_neighbors = _get_neighbors(question_vector, block_vectors)
        if not nearest_neighbors:
            return ContextBasket()
        block_filter = BlockFilter(
            ids=set([neighbor.id_ for neighbor in nearest_neighbors])
        )
        query_filter = QueryFilter(
            owner=self._owner,
            block_filter=block_filter
        )
        results = self._graph_db.get_by_filter(query_filter)
        context_basket = ContextBasket()
        if results:
            for record in results:
                block_node = _node_get(record, 'block')
                document_node = _node_get(record, 'document')
                page_id = _node_get(document_node, 'id')
                integration = _node_get(document_node, 'integration')
                content = _node_get(block_node, 'content')
                if content:
                    context_basket.append(Context(
                        content=content,
                        source=Source(page_id=page_id, integration=integration)
                    ))
        semantic_context_basket = (
            self._fetch_relevant_context_without_names(query))
        context_basket.extend(semantic_context_basket.contexts)
        print('[DataAgent] Fetched relevant context with names!')
        return context_basket

    def _fetch_exact_context(self, query: Query) -> ContextBasket:
        print('[DataAgent] Fetching exact context...')
        results = self._query_neo4j(query)
        context_basket = ContextBasket()
        if results:
            for record in results:
                block_node = _node_get(record, 'block')
                document_node = _node_get(record, 'document')
                page_id = _node_get(document_node, 'id')
                integration = _node_get(document_node, 'integration')
                content = _node_get(block_node, 'content')
                if not content:
                    continue
                context_basket.append(Context(
                    content=content,
                    source=Source(page_id=page_id, integration=integration)
                ))
        print('[DataAgent] Fetched exact context!')
        return context_basket
    
    def _fetch_relevant_to_concepts(self, query: Query) -> ContextBasket:
        print('[DataAgent] Fetching context relevant to concepts...')
        context_basket = ContextBasket()
        if not query[Concepts]:
            return context_basket

        vector_filter = self._generate_vector_filter(query)
        
        concepts: Concepts = query[Concepts]
        for concept in concepts.values:
            concept_embedding = self._openai.embed(concept)
            self._fill_basket_from_embedding(context_basket, vector_filter,
                                             concept_embedding)
        print('[DataAgent] Fetched context relevant to concepts!')
        return context_basket
    
    def _query_neo4j(self, query: Query) -> Any:
        print('[DataAgent] Querying Neo4j...')
        if not (query and query.components and query.question):
            return None
            
        integrations = None
        names = None
        time_range = None
        block_labels = None
        order_by = None
        limit = None
        if IntegrationsFilter in query.components:
            if_: IntegrationsFilter = query.components[IntegrationsFilter]
            integrations = if_.neo4j_integrations
        if PageParticipants in query.components:
            nf: PageParticipants = query.components[PageParticipants]
            names = nf.neo4j_names
        if AbsoluteTimeFilter in query.components:
            atf: AbsoluteTimeFilter = query.components[AbsoluteTimeFilter]
            time_range = atf.neo4j_time_range
        if BlocksFilter in query.components:
            bf: BlocksFilter = query.components[BlocksFilter]
            block_labels = bf.neo4j_labels
        if RelativeTimeFilter in query.components:
            rtf: RelativeTimeFilter = query.components[RelativeTimeFilter]
            order_by = rtf.neo4j_order_by
            limit = rtf.neo4j_limit
        
        if not (integrations or names or time_range or block_labels
                or order_by or limit):
            return None

        query_filter = QueryFilter(
            owner=self._owner,
            document_filter=DocumentFilter(
                integrations=integrations,
                time_range=time_range,
            ),
            name_filter=NameFilter(
                names=names
            ),
            block_filter=BlockFilter(
                labels=block_labels,
                time_range=time_range,
            ),
            order_by=order_by,
            limit=limit
        )
        results = self._graph_db.get_by_filter(query_filter)
        print('[DataAgent] Queried Neo4j!')
        return results
    
    def _generate_vector_filter(self, query: Query) -> VectorFilter:
        integrations = None
        min_date_day = None
        max_date_day = None
        block_labels = None
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

        vector_filter = VectorFilter(
            owner=self._owner,
            type=set([RowType.BLOCK]),
            min_date_day=min_date_day,
            max_date_day=max_date_day,
            integration=integrations,
            block_label=block_labels
        )
        return vector_filter
    
    def _fill_basket_from_embedding(self, context_basket: ContextBasket,
                     vector_filter: VectorFilter,
                     embedding: List[float]) -> None:
        if not (context_basket and vector_filter and embedding):
            return
        relevant_block_rows = self._vector_db.query(embedding, vector_filter)
        if not relevant_block_rows:
            return
        block_ids = [row.get('id', None) for row in relevant_block_rows]
        results = self._graph_db.get_by_filter(QueryFilter(
            owner=self._owner,
            block_filter=BlockFilter(ids=block_ids)
        ))
        # TODO Dedupe
        if results:
            for record in results:
                block_node = _node_get(record, 'block')
                document_node = _node_get(record, 'document')
                page_id = _node_get(document_node, 'id')
                integration = _node_get(document_node, 'integration')
                content = _node_get(block_node, 'content')
                if content:
                    context_basket.append(Context(
                        content=content,
                        source=Source(page_id=page_id, integration=integration)
                    ))
        return

    def _context_basket_token_size(
            self, context_basket: ContextBasket) -> int:
        token_count = 0
        for context in context_basket:
            token_count += count_tokens(context.content, self._llm.encoding_name)
        return token_count

# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def _parse_llm_response_for_query(llm_response: str) -> Query:
    match = re.search(r'{[\s\S]*}', llm_response, re.DOTALL)
    if match:
        stringified_json = match.group(0)
        query_json = json.loads(stringified_json)
        query = Query.from_llm_response(query_json)
        return query

def _format_date(date: str) -> int:
    return int(date.replace('-', ''))

def _date_day_to_timestamp(date_day: int) -> int:
    date = str(date_day)
    year = int(date[:4])
    month = int(date[4:6])
    day = int(date[6:])
    return int(datetime.datetime(year, month, day).timestamp())

def _get_today_timestamp() -> int:
    return int(datetime.datetime.today().timestamp())

def _get_today_date_day() -> int:
    return int(datetime.datetime.today().strftime('%Y%m%d'))

def _get_today_date() -> str:
    return datetime.datetime.today().strftime('%Y-%m-%d')

def _integration_name(integration: Integration) -> str:
    if integration == Integration.CRM:
        return 'zoho'
    elif integration == Integration.CUSTOMER_SUPPORT:
        return 'zendesk'
    elif integration == Integration.DOCUMENTS:
        return 'google_docs'
    elif integration == Integration.EMAIL:
        return 'google_mail'
    
def _node_get(node: Dict, property: str) -> Any:
    return node.get(property, None) if node else None

def _euclidean_distance(row1, row2):
    distance = 0.0
    for i in range(len(row1)-1):
        distance += (row1[i] - row2[i])**2
    return sqrt(distance)

@dataclass
class Vector:
    id_: str
    embedding: List[float]
    distance = float = None

def _get_neighbors(query_vector: Vector, block_vectors: List[Vector],
                  num_neighbors: int = 5) -> List[Vector]:
    query_embedding = query_vector.embedding
    for block_vector in block_vectors:
        distance = _euclidean_distance(query_embedding, block_vector.embedding)
        block_vector.distance = distance
    sorted_block_vectors = sorted(block_vectors, key=lambda x: x.distance)
    return sorted_block_vectors[:num_neighbors]

from graph.pinecone_ import Pinecone


# TODO: move to somewhere that makes sense
def _decorate_block_embeddings(_vector_db: Pinecone, documents: List[Document]) -> None:
    ids: List[str] = []
    for document in documents:
        ids.extend([consists.target.id for consists in document.consists])
    
    embeddings = _vector_db.fetch(ids)
    block_vectors = {}
    for id_, vector in embeddings.items():
        block_vectors[id_] = vector.values
    
    for document in documents:
        for consists in document.consists:
            consists.target.embedding = block_vectors.get(consists.target.id, None)

pcone = Pinecone(api_key='0ca39def-1df8-46fd-8c26-abdbe593623a', environment='us-east1-gcp')