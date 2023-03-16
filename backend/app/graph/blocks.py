from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Set


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
class Edge(ABC):
    pass

@dataclass
class Chunk(Node):
    embedding: List[float]
    content: str
    height: int

    @staticmethod
    def get_index_properties():
        return ['content', 'height']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['content'] = self.content
        map['height'] = self.height
        return map

@dataclass
class CONSISTS_OF(Edge):
    target: Chunk

@dataclass
class Document(Node):
    integration: str
    consists_of: List[CONSISTS_OF]

    @staticmethod
    def get_index_keys():
        return super(Document, Document).get_index_keys() + ['integration']
    
    @staticmethod
    def get_index_properties():
        return []

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['integration'] = self.integration
        map['chunks'] = [consist_of.target.to_neo4j_map() for consist_of in self.consists_of]
        return map

@dataclass
class DocumentFilter:
    ids: Set[str] = None
    integrations: Set[str] = None
    time_range: tuple[int, int] = None

@dataclass
class ChunkFilter:
    ids: Set[str] = None
    heights: Set[int] = None
    time_range: tuple[int, int] = None

@dataclass
class EntityFilter:
    ids: Set[str] = None
    types: Set[str] = None

@dataclass
class PredicateFilter:
    ids: Set[str] = None
    texts: Set[str] = None

@dataclass
class QueryFilter():
    owner: str
    document_filter: DocumentFilter = None
    chunk_filter: ChunkFilter = None
    entity_filter: EntityFilter = None
    predicate_filter: PredicateFilter = None

@dataclass
class PREDICATES(Edge):
    id: str
    embedding: List[float]
    text: str
    chunk: str
    document: str
    target: Node

    def to_neo4j_map(self):
        return {
            'id': self.id,
            'text': self.text,
            'chunk': self.chunk,
            'document': self.document,
            'target': self.target.to_neo4j_map(),
        }
    
@dataclass
class Entity(Node):
    type: str
    predicates: List[PREDICATES] = None

    @staticmethod
    def get_index_keys():
        return super(Document, Document).get_index_keys() + ['type']

    @staticmethod
    def get_index_properties():
        return ['type']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map['type'] = self.type
        if self.predicates:
            map['predicates'] = [predicate.to_neo4j_map() for predicate in self.predicates]
        return map