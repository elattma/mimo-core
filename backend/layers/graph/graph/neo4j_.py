import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Literal, Set

from neo4j import GraphDatabase, Record

UNIQUE_PATTERN_MIMO_PLACEHOLDER = '<UNQIUE_PLACEHOLDER>'


@dataclass
class Node(ABC):
    id: str

    @staticmethod
    @abstractmethod
    def get_index_properties():
        pass

    @staticmethod
    def get_index_keys():
        return ['id']

    def to_neo4j_map(self):
        return {
            'id': self.id,
        }


@dataclass
class Block(Node):
    embedding: List[float]
    label: str
    content: str
    last_updated_timestamp: int

    @staticmethod
    def get_index_properties():
        return ['label', 'content', 'last_updated_timestamp']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['label'] = self.label
        map['content'] = self.content
        map['last_updated_timestamp'] = self.last_updated_timestamp
        return map


@dataclass
class Consists:
    target: Block


@dataclass
class Document(Node):
    integration: str
    consists: List[Consists]

    @staticmethod
    def get_index_keys():
        return super(Document, Document).get_index_keys() + ['integration']

    @staticmethod
    def get_index_properties():
        return []

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['integration'] = self.integration
        map['blocks'] = [consist.target.to_neo4j_map()
                         for consist in self.consists]
        return map


@dataclass
class Mentioned:
    target: Document


@dataclass
class Name(Node):
    value: str
    mentioned: List[Mentioned] = None

    @staticmethod
    def get_index_keys():
        return super(Name, Name).get_index_keys()

    @staticmethod
    def get_index_properties():
        return ['value']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['value'] = self.value
        map['mentioned'] = [
            {
                'id': mentioned.target.id,
                'integration': mentioned.target.integration,
            } for mentioned in self.mentioned
        ]
        return map

    def __hash__(self):
        return hash((self.id, self.value, self.mentioned))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id and self.value == other.value and self.mentioned == other.mentioned


@dataclass
class DocumentFilter:
    ids: Set[str] = None
    integrations: Set[str] = None
    time_range: tuple[int, int] = None


@dataclass
class ContentItem:
    key: str
    value: str


@dataclass
class Matcher:
    match: str
    filter: str = None


@dataclass
class ContentMatch:
    match: str
    label: str = None
    filter: str = None

    @staticmethod
    def from_dict(matcher_dict: dict, label: str = None, filter: str = None):
        ContentMatch.replace_null_fields(matcher_dict)
        match = json.dumps(matcher_dict).replace(
            f'"{ContentMatch.get_any_match_placeholder()}"', '"([^"]*)"'
        )
        return ContentMatch(match=f'.*{match}.*', label=label, filter=filter)

    @staticmethod
    def from_contains(substring: str):
        return ContentMatch(match=f'.*{substring}.*')

    @staticmethod
    def get_entity_id_match_placeholder():
        return '<ENTITY_ID_MATCH_PLACEHOLDER>'

    @staticmethod
    def get_any_match_placeholder():
        return '<ANY_MATCH_PLACEHOLDER>'

    @staticmethod
    def replace_null_fields(dictionary: dict):
        for key, value in dictionary.items():
            if not value:
                dictionary[key] = ContentMatch.get_any_match_placeholder()
            elif isinstance(value, dict):
                ContentMatch.replace_null_fields(value)

    def __hash__(self):
        return hash((self.label))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.label == other.label


@dataclass
class BlockFilter:
    ids: Set[str] = None
    labels: Set[str] = None
    content_items: List[ContentItem] = None
    time_range: tuple[int, int] = None
    regex_matches: Set[ContentMatch] = None


@dataclass
class NameFilter:
    ids: Set[str] = None
    names: Set[str] = None


class OrderDirection(Enum):
    ASC = 'ASC'
    DESC = 'DESC'


@dataclass
class OrderBy:
    direction: OrderDirection
    node: Literal['document', 'block', 'name']
    property: Literal['last_updated_timestamp', 'id']


@dataclass
class Limit:
    offset: int
    count: int


@dataclass
class QueryFilter:
    owner: str
    document_filter: DocumentFilter = None
    block_filter: BlockFilter = None
    name_filter: NameFilter = None
    order_by: OrderBy = None
    limit: Limit = None


class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def write(self, documents: List[Document], names: List[Name], owner: str, timestamp: int):
        with self.driver.session(database='neo4j') as session:
            document_result = session.execute_write(
                self._create_document_blocks, documents, owner, timestamp=timestamp)
            names_result = session.execute_write(
                self._create_names, names, owner, timestamp=timestamp)
            return [document_result, names_result]
        
    def infer(self, names: List[Name], owner: str, timestamp: int):
        with self.driver.session(database='neo4j') as session:
            names_result = session.execute_write(self._infer_names, names, owner)
            return [names_result]

    @staticmethod
    def _get_document_merge():
        merge_object = ', '.join([f'{key}: document.{key}' for key in (
            Document.get_index_keys())]) + ', owner: $owner'
        index_properties = Document.get_index_properties()
        if index_properties and len(index_properties) > 0:
            set_object = ', '.join([f'document.{key} = document.{key}' for key in (
                Document.get_index_properties())]) + ', document.timestamp = $timestamp'
        else:
            set_object = 'document.timestamp = $timestamp'
        return (
            f'MERGE (d: Document {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
            'WITH d, document '
            'CALL { '
            'WITH d '
            'MATCH (d)-[]-(b: Block) '
            'DETACH DELETE b '
            '} '
        )

    @staticmethod
    def _get_block_merge():
        merge_object = ', '.join([f'{key}: block.{key}' for key in (
            Block.get_index_keys())]) + ', owner: $owner'
        set_object = ', '.join([f'block.{key} = block.{key}' for key in (
            Block.get_index_properties())]) + ', block.timestamp = $timestamp'
        return (
            f'MERGE (b: Block {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
            'WITH b, d, block '
            'MERGE (b)<-[:Consists]-(d) '
        )

    @staticmethod
    def _create_document_blocks(tx, documents: List[Document], owner: str, timestamp: int):
        if not (documents and len(documents) > 0 and owner and timestamp):
            return None

        neo4j_documents = [document.to_neo4j_map() for document in documents]
        documents_query = (
            'UNWIND $documents as document '
            f'{Neo4j._get_document_merge()} '
            'WITH document, d '
            'UNWIND document.blocks as block '
            f'{Neo4j._get_block_merge()} '
        )

        result = tx.run(documents_query, documents=neo4j_documents, owner=owner, timestamp=timestamp)
        return result

    @staticmethod
    def _create_names(tx, names: List[Name], owner: str, timestamp: int = None):
        if not (names and len(names) > 0 and owner):
            return None

        neo4j_names = [name.to_neo4j_map() for name in names]
        names_query = (
            'UNWIND $names as name '
            'MERGE (n: Name {id: name.id, owner: $owner}) '
            'WITH name, n '
            'CALL { '
            'WITH name, n '
            'WITH name, n '
            'WHERE name.value IS NOT NULL and n.value IS NULL '
            'SET n.value = name.value '
            '} '
            'WITH name, n '
            'UNWIND name.mentioned as mentioned '
            'MATCH (d: Document {id: mentioned.id, integration: mentioned.integration, owner: $owner}) '
            'WITH n, d '
            'MERGE (n)-[:Mentioned]->(d) '
        )

        result = tx.run(names_query, names=neo4j_names, owner=owner)
        return result
    
    @staticmethod
    def _infer_names(tx, names: List[Name], owner: str):
        if not (names and len(names) > 0 and owner):
            return None
        
        neo4j_names = [name.to_neo4j_map() for name in names]
        names_query = (
            'UNWIND $names as name '
            'MATCH (n: Name {value: name.value, owner: $owner}) '
            'WITH name, n '
            'UNWIND name.mentioned as mentioned '
            'MATCH (d: Document {id: mentioned.id, integration: mentioned.integration, owner: $owner}) '
            'WITH n, d '
            'MERGE (n)-[:Mentioned]->(d) '
        )

        result = tx.run(names_query, names=neo4j_names, owner=owner)
        return result

    def get_by_filter(self, query_filter: QueryFilter) -> List[Document]:
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._get_by_filter, query_filter)
            return result

    @staticmethod
    def _parse_record_documents(records: List[Record]) -> List[Document]:
        documents: List[Document] = []
        for record in records:
            document_node = record.get('document')
            document_id = document_node.get('id')
            document_integration = document_node.get('integration')

            consists_list = []
            for block_node in record.get('blocks'):
                block_id = block_node.get('id')
                block_label = block_node.get('label')
                block_content = block_node.get('content')
                last_updated_timestamp = block_node.get(
                    'last_updated_timestamp')
                block = Block(
                    id=block_id,
                    embedding=None,
                    label=block_label,
                    content=block_content,
                    last_updated_timestamp=last_updated_timestamp
                )
                consists = Consists(block)
                consists_list.append(consists)

            document = Document(
                id=document_id,
                integration=document_integration,
                consists=consists_list
            )
            documents.append(document)
        return documents

    # TODO: make more efficient by using params instead of injecting
    @staticmethod
    def _get_by_filter(tx, query_filter: QueryFilter) -> List[Document]:
        if not query_filter or not query_filter.owner:
            return None

        query_wheres = []

        if query_filter.owner:
            query_wheres.append(
                'document.owner = $owner AND block.owner = $owner')

        if query_filter.document_filter:
            document_filter = query_filter.document_filter
            if document_filter.ids:
                query_wheres.append(
                    f'document.id IN {list(document_filter.ids)}')
            if document_filter.integrations:
                query_wheres.append(
                    f'(document.integration IN {list(document_filter.integrations)})')
            if document_filter.time_range:
                query_wheres.append(
                    f'(document.timestamp >= {document_filter.time_range[0]} AND document.timestamp <= {document_filter.time_range[1]})')

        content_filter = ''
        if query_filter.block_filter:
            block_filter = query_filter.block_filter
            if block_filter.ids:
                query_wheres.append(
                    f'(block.id IN {list(block_filter.ids)})')
            if block_filter.labels:
                query_wheres.append(
                    f'(block.label IN {list(block_filter.labels)})')
            if block_filter.time_range:
                query_wheres.append(
                    f'(block.timestamp >= {block_filter.time_range[0]} AND block.timestamp <= {block_filter.time_range[1]})')
            if block_filter.regex_matches and query_filter.name_filter:
                content_regexes = []
                regex_matches = []
                counter = 0
                for regex_match in block_filter.regex_matches:
                    matches = []
                    if regex_match.label:
                        matches.append(f'rblock.label = "{regex_match.label}"')
                    matches.append(f'rblock.content =~ regex_{counter}')

                    content_regex = f'({" AND ".join(matches)})'
                    content_regexes.append(content_regex)
                    replaced_regex_match = regex_match.match \
                        .replace('"', '\\"') \
                        .replace('{', '\\{') \
                        .replace('}', '\\}') \
                        .replace(ContentMatch.get_entity_id_match_placeholder(), '" + name.id + "')
                    regex_match = f'"{replaced_regex_match}" AS regex_{counter}'
                    regex_matches.append(regex_match)
                    counter += 1
                content_filter = (
                    f'WITH name, document, block, {", ".join(regex_matches)} '
                    'MATCH (name)-[:Mentioned]->(document)-[:Consists]->(rblock:Block) '
                    f'WHERE {" OR ".join(content_regexes)} '
                )

        name_match = ''
        group_bys = []
        if query_filter.name_filter:
            name_match = '(name:Name)-[:Mentioned]->'
            name_filter = query_filter.name_filter
            query_wheres.append('name.owner = $owner')
            group_bys.append('COUNT(name.id) AS names_count')
            if name_filter.ids:
                query_wheres.append(f'(name.id IN {list(name_filter.ids)})')
            if name_filter.names:
                contains = []
                for name in name_filter.names:
                    contains.append(
                        f'toLower(name.value) CONTAINS "{name.lower()}"')
                contains_sub_query = ' OR '.join(contains)
                query_wheres.append(f'({contains_sub_query})')

        order_by_query = ''
        order_by = ''
        if query_filter.order_by:
            order_by = query_filter.order_by
            if order_by.property and order_by.node:
                order_by = ', max(block.last_updated_timestamp) AS order_by'
                order_by_query = 'ORDER BY order_by'
                if query_filter.order_by.direction == OrderDirection.DESC:
                    order_by_query += ' DESC'

        limit_query = ''
        if query_filter.limit:
            limit = query_filter.limit
            if limit.offset:
                limit_query += f'SKIP {limit.offset}'
            if limit.count:
                limit_query = f'LIMIT {limit.count}'

        if len(limit_query) < 1:
            limit_query = 'LIMIT 50'

        if len(query_wheres) < 1:
            return None

        # TODO: make prettier
        additional_group_bys = ''
        if group_bys:
            additional_group_bys = ', ' + ', '.join(group_bys)
        follow_up_group_by = ''
        if len(group_bys) > 0:
            follow_up_group_by += ', names_count'
        if len(order_by) > 0:
            follow_up_group_by += ', order_by'
        query = (
            f'MATCH {name_match}(document:Document)-[:Consists]->(block:Block) '
            f'WHERE {" AND ".join(query_wheres)} '
            f'{content_filter} '
            f'WITH document, block{additional_group_bys}{order_by} '
            f'WITH document, COLLECT(block) AS blocks{follow_up_group_by} '
            f'RETURN document, blocks '
            f'{order_by_query} '
            f'{limit_query} '
        )
        print('[Neo4j]: Executing query...')
        print(query)
        result = tx.run(query, owner=query_filter.owner)
        print('[Neo4j]: Query executed!')

        records = list(result)
        return Neo4j._parse_record_documents(records)