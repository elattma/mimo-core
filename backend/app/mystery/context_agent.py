import calendar
import datetime
import json
import re
from abc import ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Literal, Tuple, Union

from app.client._neo4j import (ChunkFilter, DocumentFilter, EntityFilter,
                               Neo4j, PredicateFilter, QueryFilter)
from app.client._openai import OpenAI
from app.client._pinecone import Filter as VectorFilter
from app.client._pinecone import Pinecone, RowType
from app.mrkl.llm import LLM
from app.mrkl.open_ai import OpenAIChat
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)
from neo4j import Record

now = datetime.datetime.now()
last_day_of_month = calendar.monthrange(year=int(now.strftime("%Y")), month=int(now.strftime("%m")))[1]

SYSTEM_MESSAGE = '''Pretend you are a consultant brought in to help query data.
You are an expert at using knowledge graphs and vector databases.

Your job is use the data tools below to retrieve data based on a query.
Each tool is listed below. You must only use the tools below.

For reference:
It is currently {todays_time} on {todays_date}. (use 24-hour clock)
The company has integrated the following data sources: 
Gmail for mail, Google Docs for documents, Salesforce for customer relationship manager, and Zendesk for customer support tickets.

Some tips to help you:
A company has extracted all information from the following data sources and stored it both a knowledge graph and a vector database.
If you are handling a relationship between multiple entities, I suggest using the vector database and output "knowledge_triplet_ids".
If you don't know what to do, use the vector database and output "chunk_ids".
The final step of your output should always be to use the Document Graph.
Remember to only use the tools below. And you must use the response format of the examples.
--------
Tool documentation:
# Used to query a knowledge graph based on a specific keywords
# Returns either IDs of chunks of text or knowledge triplets connected to that node
{{
 "action": "Knowledge Graph on Keywords",
 "input": {{
  "keywords": List[str]
 }},
 "output": {{
  type: "chunk_ids" | "knowledge_triplet_ids"
 }}
}}

# Used to query a knowledge graph based on a set of knowledge_triplet_ids from the graph
# Returns the respective chunk IDs or document IDs
{{
 "action": "Knowledge Graph on Triplet IDs",
 "output": {{
  "type": "chunk_ids" | "document_ids"
 }}
}}

# Used to retrieve text
# Optionally can enter chunk IDs or document IDs
# Return chunks of text, entire documents, or summaries of the text
{{
 "action": "Document Graph",
 # Can add as many as are helpful
 "optional_filters": {{
  "ids_type": "chunk_ids" | "document_ids"
  "data_sources": List[str]
  "time_frame": ["YYYY-MM-DD", "YYYY-MM-DD"]
 }},
 "output": {{
  "type": "chunk_text" | "document_text" | "summary_text",
 }}
}}

# Used to get the most semantically similar
# Output "chunk_ids" if looking for the most relevant chunk of text to a query
# Output "knowledge_triplet_ids" if looking for a relationship or action by an entity
{{
 "action": "Vector Database",
 "input": {{
  "query": str
 }},
 # Can add as many as are helpful
 "optional_filters": {{
  "document_ids": List[str],
  "data_sources": List[str],
  "time_frame": ["YYYY-MM-DD", "YYYY-MM-DD"]
 }},
 "output": {{
  "type": "chunk_ids" | "knowledge_triplet_ids"
 }}
}}
--------
You must used the output format shown in the examples below:

Query: Return all emails involving cargo.one in the last week.
Response:
[
 {{
  "action": "Knowledge Graph on Keyword",
  "input": {{
   "keywords": ["cargo.one"]
  }},
  "output": {{
   "type": "chunk_ids"
  }}
 }},
 {{
  "action": "Document Graph",
  "optional_filters": {{
   "ids_type": "chunk_ids",
   "data_sources": ["Gmail"],
   "time_frame": ["{last_week_start}", "{todays_date}"]
  }},
  "output": {{
   "type": "document_text"
  }}
 }}
]

Query: Today's Intercom tickets.
Response:
[
 {{
  "action": "Document Graph",
  "optional_filters": {{
   "data_sources": ["Intercom"],
   "time_frame": ["{todays_date}", "{todays_date}"]
  }},
  "output": {{
   type: "document_text"
  }}
 }}
]

Query: All Intercom tickets from this month of a customer complaining about the new product
Response:
[
 {{
  "action": "Vector Database",
  "input": {{
   "query": "customer complaining about the new product"
  }},
  "optional_filters": {{
   "data_sources": ["Intercom"],
   "time_range": ["{this_month_start}", "{this_month_end}"]
  }},
  "output": {{
   "knowledge_triplet_ids"
  }}
 }},
 {{
  "action": "Knowledge Graph on Triplet IDs",
  "input": {{
   "knowledge_triplet_ids": List[str]
  }},
  "output": {{
    type: "document_ids"
  }}
 }},
 {{
  "action": "Document Graph",
  "optional_filters": {{
   "ids": "document_ids"
  }},
  "output": {{
   type: "document_text"
  }}
 }}
]'''.format(
    todays_date = now.strftime('%Y-%m-%d'),
    todays_time = now.strftime('%H:%M:%S'),
    last_week_start = (now - datetime.timedelta(days=6)).strftime('%Y-%m-%d'),
    this_month_start = now.strftime('%Y-%m-01'),
    this_month_end = now.strftime(f'%Y-%m-{last_day_of_month}')
)

class ContextAgentError(Enum):
    # TODO: Make these the actual responses that the user will see
    CREATE_ACTION_ERROR = 'Error creating action'
    PARSE_PLAN_ERROR = 'Error parsing plan'
    EXECUTE_PLAN_ERROR = 'Error executing plan'

@dataclass
class Context:
    content: str

class ActionName(Enum):
    KNOWLEDGE_GRAPH_ON_KEYWORDS = 'Knowledge Graph on Keywords'
    KNOWLEDGE_GRAPH_ON_TRIPLET_IDS = 'Knowledge Graph on Triplet IDs'
    DOCUMENT_GRAPH = 'Document Graph'
    VECTOR_DATABASE = 'Vector Database'

class Action(ABC):
    @classmethod
    def create_action_from_step(cls, step: Dict[str, Any]) -> Any:
        action_name = step.get('action', None) if step else None

        if action_name == ActionName.KNOWLEDGE_GRAPH_ON_KEYWORDS.value:
            keywords = step.get('input', {}).get('keywords', [])
            output_type = step.get('output', {}).get('type', None)
            if not keywords or not output_type:
                return ContextAgentError.CREATE_ACTION_ERROR
            return KnowledgeGraphOnKeywordsAction(
                keywords=keywords,
                output_type=IdType(output_type)
            )
        elif action_name == ActionName.KNOWLEDGE_GRAPH_ON_TRIPLET_IDS.value:
            output_type = step.get('output', {}).get('type', None)
            if not output_type:
                return ContextAgentError.CREATE_ACTION_ERROR
            return KnowledgeGraphOnTripletsAction(
                output_type=IdType(output_type)
            )
        elif action_name == ActionName.DOCUMENT_GRAPH.value:
            output_type = step.get('output', {}).get('type', None)
            optional_filters = step.get('optional_filters', {})
            return DocumentGraphAction(
                output_type=TextType(output_type),
                optional_filters=Filters.from_dict(optional_filters)
            )
        elif action_name == ActionName.VECTOR_DATABASE.value:
            query = step.get('input', {}).get('query', None)
            output_type = step.get('output', {}).get('type', None)
            if not output_type or not query:
                return ContextAgentError.CREATE_ACTION_ERROR
            optional_filters = step.get('optional_filters', {})
            return VectorDatabaseAction(
                query=query,
                output_type=IdType(output_type),
                optional_filters=Filters.from_dict(optional_filters)
            )
        else:
            return ContextAgentError.CREATE_ACTION_ERROR

class IdType(Enum):
    KNOWLEDGE_TRIPLET = 'knowledge_triplet_ids'
    CHUNK = 'chunk_ids'
    DOCUMENT = 'document_ids'

class TextType(Enum):
    CHUNK_TEXT = 'chunk_text'
    DOCUMENT_TEXT = 'document_text'
    SUMMARY_TEXT = 'summary_text'

@dataclass
class Filters:
    ids_type: IdType = None
    document_ids: List[str] = None
    data_sources: List[str] = None
    time_frame: Tuple[str, str] = None

    @staticmethod
    def from_dict(dict: Dict[str, Any]):
        filters = Filters()
        for key, value in dict.items():
            if key == 'ids_type':
                filters.ids_type = IdType(value)
            if key == 'document_ids':
                filters.document_ids = value
            elif key == 'data_sources':
                filters.data_sources = value
            elif key == 'time_frame':
                filters.time_frame = value
        return filters

@dataclass
class KnowledgeGraphOnKeywordsAction(Action):
    keywords: List[str]
    output_type: Union[
        Literal[IdType.CHUNK], 
        Literal[IdType.KNOWLEDGE_TRIPLET]
    ]

@dataclass
class KnowledgeGraphOnTripletsAction(Action):
    output_type: Union[Literal[IdType.CHUNK], Literal[IdType.DOCUMENT]]

@dataclass
class DocumentGraphAction(Action):
    output_type: Union[
        Literal[TextType.CHUNK_TEXT],
        Literal[TextType.DOCUMENT_TEXT],
        Literal[TextType.SUMMARY_TEXT]
    ]
    optional_filters: Filters = None

@dataclass
class VectorDatabaseAction(Action):
    query: str
    output_type: Union[
        Literal[IdType.CHUNK], 
        Literal[IdType.KNOWLEDGE_TRIPLET]
    ]
    optional_filters: Filters = None
            
class ContextAgent():
    def __init__(
        self,
        llm: OpenAIChat,
        owner: str,
        graph_db: Neo4j,
        vector_db: Pinecone,
        openai_client: OpenAI
    ) -> None:
        self._llm: OpenAIChat = llm
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai_client: OpenAI = openai_client
        self._contexts: Dict[str, Context] = {}

    def run(self, query: str) -> Union[str, ContextAgentError]:
        self._prepare_for_new_lifecycle()
        # 1. Call GPT-4 to make a plan
        plan: str = self._create_plan(query)
        print('--------CONTEXT AGENT: PLAN--------')
        print(plan)
        print()
        # 2. Parse plan
        actions = _parse_plan(plan)
        print("-------------CONTEXT AGENT: ACTIONS-------------")
        print(actions)
        print()
        if isinstance(actions, ContextAgentError):
            return actions
        
        context = self._perform_actions(actions)
        print('-------------CONTEXT AGENT: CONTEXT-------------')
        print(context)
        print()

        return context


    def _prepare_for_new_lifecycle(self) -> None:
        self._contexts = {}

    def _create_plan(self, query: str) -> str:
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=SYSTEM_MESSAGE
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=f'Query: {query}\nResponse:\n'
        )
        prompt = ChatPrompt(messages=[system_message, user_message])
        return self._llm.predict(prompt=prompt)
    
    def _perform_actions(self, actions: List[Action]) -> str:
        state: Dict[str, Any] = None
        for action in actions:
            print('-------------CONTEXT AGENT: STATE-------------')
            print(state)
            print()
            if isinstance(action, KnowledgeGraphOnKeywordsAction):
                state = self._knowledge_graph_on_keywords(action)
            elif isinstance(action, KnowledgeGraphOnTripletsAction):
                triplet_ids = state.get(IdType.KNOWLEDGE_TRIPLET, None) if state else None
                if not triplet_ids:
                    return ContextAgentError.EXECUTE_PLAN_ERROR
                state = self._knowledge_graph_on_triplet_ids(action, triplet_ids)
            elif isinstance(action, DocumentGraphAction):
                ids = state.get('ids', None) if state else None
                print('-------------CONTEXT AGENT: IDS-------------')
                print(ids)
                print()
                if not ids:
                    return ContextAgentError.EXECUTE_PLAN_ERROR
                state = self._document_graph(action, ids)
                print('-------------CONTEXT AGENT: STATE AFTER DOCUMENT GRAPH RETURN-------------')
                print(state)
                print()
            elif isinstance(action, VectorDatabaseAction):
                state = self._vector_database(action)
            else:
                raise Exception('Invalid action')
        return '\n\n'.join(state.get('texts', [])) if state else ''

    def _knowledge_graph_on_keywords(self, action: KnowledgeGraphOnKeywordsAction) -> Dict[str, Any]:
        query_filter = QueryFilter(
            owner=self._owner,
            entity_filter=EntityFilter(
                ids=action.keywords
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(query_filter=query_filter)
        ids = set()
        if action.output_type == IdType.CHUNK:
            for record in results:
                predicate_node = record.get('p', None) if record else None
                chunk_id = predicate_node.get('chunk', None) if predicate_node else None
                if not chunk_id:
                    continue
                ids.add(chunk_id)
        elif action.output_type == IdType.KNOWLEDGE_TRIPLET:
            for record in results:
                predicate_node = record.get('p', None) if record else None
                predicate_id = predicate_node.get('id', None) if predicate_node else None
                if not predicate_id:
                    continue
                ids.add(predicate_id)

        return {
            'ids': list(ids)
        }

    def _knowledge_graph_on_triplet_ids(self, action: KnowledgeGraphOnTripletsAction, triplet_ids: List[str]) -> Dict[str, Any]:
        query_filter = QueryFilter(
            owner=self._owner,
            predicate_filter=PredicateFilter(
                ids=triplet_ids
            )
        )
        results: List[Record] = self._graph_db.get_by_filter(query_filter=query_filter)
        ids = set()
        if action.output_type == IdType.CHUNK:
            for record in results:
                predicate_node = record.get('p', None) if record else None
                chunk_id = predicate_node.get('chunk', None) if predicate_node else None
                if not chunk_id:
                    continue
                ids.add(chunk_id)
        elif action.output_type == IdType.DOCUMENT:
            for record in results:
                predicate_node = record.get('p', None) if record else None
                document_id = predicate_node.get('document', None) if predicate_node else None
                if not document_id:
                    continue
                ids.add(document_id)

        return {
            'ids': list(ids)
        }
    
    def _document_graph(self, action: DocumentGraphAction, ids: List[str]) -> Dict[str, Any]:
        document_filter = DocumentFilter()
        chunk_filter = ChunkFilter()
        if action.optional_filters:
            if action.optional_filters.data_sources:
                document_filter.integrations = action.optional_filters.data_sources
            if action.optional_filters.time_frame:
                time_start = datetime.datetime.strptime(action.optional_filters.time_frame[0], '%Y-%m-%d')
                time_end = datetime.datetime.strptime(action.optional_filters.time_frame[1], '%Y-%m-%d')
                document_filter.time_range = (int(time_start.timestamp()), int(time_end.timestamp()))
                chunk_filter.time_range = (int(time_start.timestamp()), int(time_end.timestamp()))

        if action.optional_filters.ids_type == IdType.CHUNK:
            chunk_filter.ids = set(ids)
            print('-------------CONTEXT AGENT: CHUNK FILTER-------------')
            print(chunk_filter)
            print()
        elif action.optional_filters.ids_type == IdType.DOCUMENT:
            document_filter.ids = set(ids)

        query_filter = QueryFilter(
            owner=self._owner,
            chunk_filter=chunk_filter,
            document_filter=document_filter
        )
        print('-------------CONTEXT AGENT: QUERY FILTER-------------')
        print(query_filter)
        print()
        results: List[Record] = self._graph_db.get_by_filter(query_filter=query_filter)
        print('-------------CONTEXT AGENT: RESULTS-------------')
        print(results)
        print()
        if not results or len(results) == 0:
            return None
        texts: List[str] = []
        if action.output_type == TextType.CHUNK_TEXT or action.output_type == TextType.DOCUMENT_TEXT:
            for record in results:
                chunk_node = record.get('c', None) if record else None
                content = chunk_node.get('content', None) if chunk_node else None
                if not content:
                    continue
                texts.append(content)
        elif action.output_type == TextType.SUMMARY_TEXT:
            document_id_height_map = {}
            document_id_content_map = {}
            for record in results:
                document_node = record.get('d', None) if record else None
                document_id = document_node.get('id', None) if document_node else None
                chunk_node = record.get('c', None) if record else None
                content = chunk_node.get('content', None) if chunk_node else None
                height = chunk_node.get('height', 0) if chunk_node else 0
                if not (document_id and content and height):
                    continue
                if document_id not in document_id_height_map:
                    document_id_height_map[document_id] = height
                    document_id_content_map[document_id] = content
                elif document_id_height_map[document_id] < height:
                    document_id_height_map[document_id] = height
                    document_id_content_map[document_id] = content
            texts = list(document_id_content_map.values())
        
        print(texts)
        return {
            'texts': texts
        }
    
    def _vector_database(self, action: VectorDatabaseAction) -> Dict[str, Any]:
        embedding = self._openai_client.embed(action.query)

        query_filter = VectorFilter(
            owner=self._owner,
            type=[RowType.TRIPLET if action.output_type == IdType.KNOWLEDGE_TRIPLET else RowType.CHUNK]
        )

        if action.optional_filters:
            if action.optional_filters.data_sources:
                query_filter.integration = action.optional_filters.data_sources
            if action.optional_filters.document_ids:
                query_filter.document_id = action.optional_filters.document_ids
            if action.optional_filters.time_frame:
                time_start = datetime.datetime.strptime(action.optional_filters.time_frame[0], '%Y-%m-%d')
                time_end = datetime.datetime.strptime(action.optional_filters.time_frame[1], '%Y-%m-%d')
                query_filter.min_max_date_day = (int(time_start.timestamp()), int(time_end.timestamp()))

        results = self._vector_db.query(
            embedding=embedding,
            query_filter=query_filter,
            k=20 if action.output_type == IdType.KNOWLEDGE_TRIPLET else 3
        )
        ids: List[str] = [neighbor.get('id', None) if neighbor else None for neighbor in results]
        return {
            'ids': ids
        }

def _parse_plan(
    plan: str
) -> Union[List[Action], ContextAgentError]:
    '''Parse the plan from GPT-4 into a list of actions.'''
    pattern = r"\[\n(.*)[\n\]]"
    match = re.search(pattern, plan, re.DOTALL)
    if match is None:
        return ContextAgentError.PARSE_PLAN_ERROR
    try:
        parsed_plan = json.loads('[\n' + match.group(1).strip() + '\n]')
    except:
        return ContextAgentError.PARSE_PLAN_ERROR
    actions = [Action.create_action_from_step(step) for step in parsed_plan]

    return actions