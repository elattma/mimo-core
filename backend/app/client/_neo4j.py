from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Set

from neo4j import GraphDatabase


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
        map['blocks'] = [consist.target.to_neo4j_map() for consist in self.consists]
        return map
    
@dataclass
class DocumentFilter:
    ids: Set[str] = None
    integrations: Set[str] = None
    time_range: tuple[int, int] = None

@dataclass
class BlockFilter:
    ids: Set[str] = None
    labels: Set[str] = None
    time_range: tuple[int, int] = None

@dataclass
class QueryFilter:
    owner: str
    document_filter: DocumentFilter = None
    block_filter: BlockFilter = None

class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_document_blocks(self, documents: List[Document], owner: str, timestamp: int):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._create_document_blocks, documents, owner, timestamp=timestamp)
            return result

    @staticmethod
    def _get_document_merge():
        merge_object = ', '.join([f'{key}: document.{key}' for key in (
            Document.get_index_keys())]) + ', owner: $owner'
        index_properties = Document.get_index_properties()
        if index_properties and len(index_properties) > 0:
            set_object = ', '.join([f'd.{key} = document.{key}' for key in (
                Document.get_index_properties())]) + ', d.timestamp = $timestamp'
        else:
            set_object = 'd.timestamp = $timestamp'
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
        set_object = ', '.join([f'b.{key} = block.{key}' for key in (
            Block.get_index_properties())]) + ', b.timestamp = $timestamp'
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
        
    def get_by_filter(self, query_filter: QueryFilter) -> Any:
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._get_by_filter, query_filter)
            return result

    @staticmethod
    def _get_by_filter(tx, query_filter: QueryFilter) -> List[Block]:
        if not query_filter or not query_filter.owner:
            return None

        document_query_wheres = []
        if query_filter.owner:
            document_query_wheres.append('d.owner = $owner AND b.owner = $owner')

        if query_filter.document_filter:
            document_filter = query_filter.document_filter
            if document_filter.ids:
                document_query_wheres.append(
                    f'd.id IN {list(document_filter.ids)}')
            if document_filter.integrations:
                document_query_wheres.append(
                    f'(d.integration IN {list(document_filter.integrations)})')
            if document_filter.time_range:
                document_query_wheres.append(
                    f'(d.timestamp >= {document_filter.time_range[0]} AND d.timestamp <= {document_filter.time_range[1]})')

        if query_filter.block_filter:
            block_filter = query_filter.block_filter
            if block_filter.ids:
                document_query_wheres.append(
                    f'(b.id IN {list(block_filter.ids)})')
            if block_filter.labels:
                document_query_wheres.append(
                    f'(b.label IN {list(block_filter.labels)})')
            if block_filter.time_range:
                document_query_wheres.append(
                    f'(d.timestamp >= {block_filter.time_range[0]} AND d.timestamp <= {block_filter.time_range[1]})')

        if len(document_query_wheres) < 1:
            return None

        query = ''
        query += (
            'MATCH (d: Document)-[co:Consists]->(b: Block) '
            f'WHERE {" AND ".join(document_query_wheres)} '
        )
        query += 'RETURN '
        query += 'd, co, b'
        result = tx.run(query, owner=query_filter.owner)
        return list(result)