import datetime
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
from typing import Dict, List

from app.client._neo4j import Neo4j, QueryFilter, BlockFilter
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone, Filter, RowType
from app.mrkl.open_ai import OpenAIChat
from app.mrkl.prompt import (ChatPrompt, ChatPromptMessage,
                             ChatPromptMessageRole)

SYSTEM_MESSAGE = '''You are DataGPT, a large language model that is an expert at retrieving data from a specialized database.
Your job is to examine a Question and produce a well-formed Query for the database.

A Query consists of four optional components that can be derived from the Question.
1. `entities`: Any named entities that are explicitly mentioned in the Question.
2. `time_frame`: A period of time that the Question specifies. It is currently 11:52 AM on Monday, 2023-03-27.
3. `sources`: Any data sources that are implicitly or explicitly mentioned in the Question.
4. `blocks`: The database divides its source documents into different blocks. `blocks` is a list of these blocks that the Question explicitly or implicitly mentioned.

The available data sources are {data_sources}.

The available blocks are:
{block_descriptions}

A well-formed Query is a JSON object and should look like this:
{{
 "entities": {{
  "name": str,
  "links": str[]
 }}[],
 "time_frame": str[], // [start_date, end_date]
 "sources": str[],
 "blocks": str[]
}}

Use the examples below to help you understand how to write a Query.
EXAMPLES:
Question: What is the subject of the email John Doe sent me yesterday?
Query:
{{
 "entities": [{{
  "name": "John Doe",
  "links": []
 }}],
 "time_frame": ["2023-03-26", "2023-03-26"],
 "sources": ["email"],
 "blocks": ["title"]
}}

Question: Which customers bought a product last week?
Query:
{{
 "time_frame": ["2023-03-19", "2023-03-25"],
 "sources": ["crm"]
}}

Question: How does Troy Wilkerson feel about his manager?
Query:
{{
 "entities": [{{
  "name": "Troy Wilkerson",
  "links": ["feel", "manager"]
 }}]
}}
'''

USER_MESSAGE = 'Question: {question}'

SOURCE_TO_INTEGRATIONS = {
    'email': ['google_mail'],
    'documents': ['google_docs', 'upload'],
    'crm': ['zoho'],
    'customer_support': ['zendesk']
}

@dataclass
class Entity:
    name: str
    links: List[str]

    @staticmethod
    def from_dict(entity_dict: Dict):
        if not entity_dict:
            return None

        name = entity_dict.get('name', None)
        links = entity_dict.get('links', None)

        if not (name and links):
            return None

        return Entity(name=name, links=links)

@dataclass
class TimeFrame:
    # TODO: Figure out how to represent time frames
    start_date: str
    end_date: str

    @staticmethod
    def from_list(time_frame_list: List[str]):
        if not time_frame_list:
            return None

        start_date = time_frame_list[0]
        end_date = time_frame_list[1]

        return TimeFrame(start_date=start_date, end_date=end_date)

@dataclass
class Query:
    entities: List[Entity]
    time_frame: TimeFrame
    sources: List[str]
    blocks: List[str]
    raw_input: str = None

    @staticmethod
    def from_dict(query_dict: Dict):
        if not query_dict:
            return None

        entities = query_dict.get('entities', None)
        time_frame = query_dict.get('time_frame', None)
        sources = query_dict.get('sources', None)
        blocks = query_dict.get('blocks', None)

        return Query(
            entities=[Entity.from_dict(entity) for entity in entities] 
            if entities and len(entities) > 0 else None,
            time_frame=TimeFrame.from_list(time_frame)
            if time_frame and len(time_frame) == 2 else None,
            sources=sources,
            blocks=blocks
        )

@dataclass
class BlockDescription:
    name: str
    description: str

@dataclass
class Context:
    content: str

@dataclass
class ContextBasket:
    contexts: List[Context]

class DataAgent(ABC):
    '''The data agent abstract class.'''
    def __init__(
        self,
        llm: OpenAIChat,
        owner: str,
        graph_db: Neo4j,
        vector_db: Pinecone,
        openai: OpenAI
    ) -> None:
        self._llm: OpenAIChat = llm
        self._owner: str = owner
        self._graph_db: Neo4j = graph_db
        self._vector_db: Pinecone = vector_db
        self._openai: OpenAI = openai

    def create_query(
        self,
        mystery: str,
        data_sources: List[str],
        block_descriptions: List[BlockDescription]
    ) -> Query:
        '''Create a query from a mystery.

        Args:
            mystery (str): The mystery to create a query from.
            data_sources (List[str]): The data sources in the database.

        Returns:
            Query: The query.
        '''
        prompt = self._generate_prompt(
            mystery,
            data_sources,
            block_descriptions
        )
        response = self._llm.predict(prompt=prompt)
        query = _parse_llm_response_for_query(response)
        return query
    
    def execute_query(self, query: Query) -> ContextBasket:
        '''Execute a query.

        Args:
            query (Query): The query to execute.

        Returns:
            ContextBasket: The result of the query.
        '''
        if not query:
            return None
        query_embedding = self._openai.embed(query.raw_input)
        integrations = []
        if query.sources:
            for source in query.sources:
                integrations.extend(SOURCE_TO_INTEGRATIONS[source])
        if query.time_frame:
            min_date = _get_timestamp_from_date(query.time_frame.start_date)
            max_date = _get_timestamp_from_date(query.time_frame.end_date)
        filter = Filter(
            owner=self._owner,
            integration=set(integrations) if integrations else None,
            type=[RowType.BLOCK],
            min_max_date_day=(min_date, max_date)
            if query.time_frame else None
        )
        neighbors = self._vector_db.query(
            query_embedding, 
            query_filter=filter
        )
        block_filter = BlockFilter(
            ids=set([neighbor.id for neighbor in neighbors]),
            labels=set(query.blocks) if query.blocks else None,
        )
        query_filter = QueryFilter(
            owner=self._owner,
            block_filter=block_filter
        )
        results = self._graph_db.get_by_filter(query_filter)
        print(results)


    def _generate_prompt(
        self,
        mystery: str,
        data_sources: List[str],
        block_descriptions: List[BlockDescription]
    ) -> ChatPrompt:
        data_sources = '[' + ', '.join(data_sources) + ']'
        block_descriptions = '\n'.join([
            f'{i + 1}: {block.name}: {block.description}'
            for i, block in enumerate(block_descriptions)
        ])
        system_message = ChatPromptMessage(
            role=ChatPromptMessageRole.SYSTEM.value,
            content=SYSTEM_MESSAGE.format(
                data_sources=data_sources,
                block_descriptions=block_descriptions
            )
        )
        user_message = ChatPromptMessage(
            role=ChatPromptMessageRole.USER.value,
            content=USER_MESSAGE.format(question=mystery)
        )
        prompt = ChatPrompt(
            messages=[system_message, user_message]
        )
        return prompt
    
def _parse_llm_response_for_query(query: str) -> Query:
    regex = r'Query:\s*{(.*)}'
    match = re.search(regex, query, re.DOTALL)
    if match:
        query_str = '{' + match.group(1) + '}'
        query_dict = json.loads(query_str)
        query = Query.from_dict(query_dict)
        return query
    
def _get_timestamp_from_date(date: str) -> int:
    return int(time.mktime(
        datetime.datetime.strptime(
            date, '%Y-%m-%d'
        ).timetuple()
    )) * 1000