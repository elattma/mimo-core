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

    @staticmethod
    def get_index_properties():
        return ['label', 'content']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['label'] = self.label
        map['content'] = self.content
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
    
# @dataclass
# class Predicate(Edge):
#     id: str
#     embedding: List[float]
#     text: str
#     documents: List[str]
#     target: Node

#     def to_neo4j_map(self):
#         return {
#             'id': self.id,
#             'text': self.text,
#             'block': self.block,
#             'document': self.document,
#             'target': self.target.to_neo4j_map(),
#         }
    
# @dataclass
# class Entity(Node):
#     type: str
#     predicates: List[Predicate] = None

#     @staticmethod
#     def get_index_keys():
#         return super(Document, Document).get_index_keys() + ['type']

#     @staticmethod
#     def get_index_properties():
#         return ['type']

#     def to_neo4j_map(self):
#         map = super().to_neo4j_map()
#         map['type'] = self.type
#         if self.predicates:
#             map['predicates'] = [predicate.to_neo4j_map() for predicate in self.predicates]
#         return map

@dataclass
class DocumentFilter:
    ids: Set[str] = None
    integrations: Set[str] = None
    time_range: tuple[int, int] = None

@dataclass
class blockFilter:
    ids: Set[str] = None
    heights: Set[int] = None
    time_range: tuple[int, int] = None

# @dataclass
# class EntityFilter:
#     ids: Set[str] = None
#     types: Set[str] = None

# @dataclass
# class PredicateFilter:
#     ids: Set[str] = None
#     texts: Set[str] = None

@dataclass
class QueryFilter:
    owner: str
    document_filter: DocumentFilter = None
    block_filter: blockFilter = None
    # entity_filter: EntityFilter = None
    # predicate_filter: PredicateFilter = None

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

    # def create_entities(self, entities: List[Entity], owner: str, timestamp: int):
    #     with self.driver.session(database='neo4j') as session:
    #         result = session.execute_write(
    #             self._create_entities, entities, documents, owner, timestamp=timestamp)
    #         return result

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
        

    # @staticmethod
    # def _get_entity_merge():
    #     predicate_merge = 'text: predicate.text, document: predicate.document'
    #     subject_merge = ', '.join([f'{key}: entity.{key}' for key in (
    #         Entity.get_index_keys())]) + ', owner: $owner'
    #     object_merge = ', '.join([f'{key}: predicate.target.{key}' for key in (
    #         Entity.get_index_keys())]) + ', owner: $owner'
    #     set_object = 'p.block=predicate.block, p.id=predicate.id'
    #     return (
    #         'UNWIND $entities as entity '
    #         'WITH entity '
    #         'UNWIND entity.predicates as predicate '
    #         f'MERGE (s:Entity {{{subject_merge}}}) '
    #         'WITH s, predicate '
    #         f'MERGE (o:Entity {{{object_merge}}}) '
    #         'WITH s, o, predicate '
    #         f'MERGE (s)-[p:Predicate {{{predicate_merge}}}]->(o) '
    #         'ON CREATE '
    #         f'SET {set_object} '
    #         'ON MATCH '
    #         f'SET {set_object} '
    #     )

    # @staticmethod
    # def _create_entities(tx, entities: List[Entity], documents: List[Document], owner: str, timestamp: int):
    #     if not (entities and len(entities) > 0 and documents and len(documents) > 0):
    #         return None

    #     neo4j_documents = [document.to_neo4j_map() for document in documents]
    #     documents_query = (
    #         'UNWIND $documents as document '
    #         f'{Neo4j._get_document_merge()}'
    #         'WITH document, d '
    #         'CALL { '
    #         'WITH d '
    #         'MATCH ()-[p:Predicate {document: d.id}]-() '
    #         'DELETE p '
    #         '} '
    #         'UNWIND document.blocks as block '
    #         f'{Neo4j._get_block_merge()} '
    #     )
    #     documents_result = tx.run(
    #         documents_query, documents=neo4j_documents, timestamp=timestamp, owner=owner)
    #     neo4j_entities = [entity.to_neo4j_map() for entity in entities]
    #     entities_result = tx.run(Neo4j._get_entity_merge(), entities=neo4j_entities, timestamp=timestamp, owner=owner)
    #     return list(entities_result) + list(documents_result)

    def get_by_filter(self, query_filter: QueryFilter) -> Any:
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._get_by_filter, query_filter)
            return result

    # @staticmethod
    # def _get_by_filter(tx, query_filter: QueryFilter) -> List[block]:
    #     if not query_filter or not query_filter.owner:
    #         return None

    #     document_query_wheres = []
    #     entity_query_wheres = []
    #     if query_filter.owner:
    #         document_query_wheres.append(
    #             'd.owner = $owner AND c.owner = $owner')
    #         entity_query_wheres.append('s.owner = $owner AND o.owner = $owner')

    #     if query_filter.document_filter:
    #         document_filter = query_filter.document_filter
    #         if document_filter.ids:
    #             document_query_wheres.append(
    #                 f'd.id IN {list(document_filter.ids)}')
    #         if document_filter.integrations:
    #             document_query_wheres.append(
    #                 f'(d.integration IN {list(document_filter.integrations)})')
    #         if document_filter.time_range:
    #             document_query_wheres.append(
    #                 f'(d.timestamp >= {document_filter.time_range[0]} AND d.timestamp <= {document_filter.time_range[1]})')

    #     if query_filter.block_filter:
    #         block_filter = query_filter.block_filter
    #         if block_filter.ids:
    #             document_query_wheres.append(
    #                 f'(c.id IN {list(block_filter.ids)})')
    #         if block_filter.heights:
    #             document_query_wheres.append(
    #                 f'(c.height IN {list(block_filter.heights)})')
    #         if block_filter.time_range:
    #             document_query_wheres.append(
    #                 f'(d.timestamp >= {block_filter.time_range[0]} AND d.timestamp <= {block_filter.time_range[1]})')

    #     if query_filter.entity_filter:
    #         entity_filter = query_filter.entity_filter
    #         if entity_filter.ids:
    #             entity_query_wheres.append(
    #                 f'(s.id IN {list(entity_filter.ids)} OR o.id IN {list(entity_filter.ids)})')
    #         if entity_filter.types:
    #             entity_query_wheres.append(
    #                 f'(s.types IN {list(entity_filter.types)} OR o.types IN {list(entity_filter.types)})')

    #     if query_filter.predicate_filter:
    #         predicate_filter = query_filter.predicate_filter
    #         if predicate_filter.ids:
    #             entity_query_wheres.append(
    #                 f'(p.id IN {list(predicate_filter.ids)})')
    #         if predicate_filter.texts:
    #             entity_query_wheres.append(
    #                 f'(p.types IN {list(predicate_filter.texts)})')

    #     if len(document_query_wheres) + len(entity_query_wheres) < 1:
    #         return None

    #     query = ''
    #     has_document_query = len(document_query_wheres) > 1
    #     has_entity_query = len(entity_query_wheres) > 1
    #     if has_document_query:
    #         query += (
    #             'MATCH (d: Document)-[co:Consists]->(b: Block) '
    #             f'WHERE {" AND ".join(document_query_wheres)} '
    #         )
    #         if has_entity_query:
    #             query += 'WITH d, co, c '

    #     if has_entity_query:
    #         query += (
    #             'MATCH (s: Entity)-[p:Predicate]->(o: Entity) '
    #             f'WHERE {" AND ".join(entity_query_wheres)} '
    #         )
    #     if not query:
    #         return None

    #     query += 'RETURN '
    #     if has_document_query:
    #         query += 'd, co, c'
    #         if has_entity_query:
    #             query += ', '
    #     if has_entity_query:
    #         query += 's, p, o'
    #     result = tx.run(query, owner=query_filter.owner)
    #     return list(result)