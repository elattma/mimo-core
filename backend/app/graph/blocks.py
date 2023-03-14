from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Set


@dataclass
class Access:
    id: str
    type: str

@dataclass
class Node(ABC):
    id: Any
    user: str

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
class ProperNoun(Node):
    type: str

    @staticmethod
    def get_index_properties():
        return ['type']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map.update({
            'type': self.type
        })
        return map

@dataclass
class REFERENCES(Edge):
    target: ProperNoun

@dataclass
class Chunk(Node):
    embedding: List[float]
    content: str
    type: str
    references: List[REFERENCES]

    @staticmethod
    def get_index_properties():
        return ['content', 'type']

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map.update({
            'content': self.content,
            'type': self.type,
            'propernouns': [ref.target.to_neo4j_map() for ref in self.references]
        })
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
        map.update({
            'integration': self.integration,
            'chunks': [chunk.target.to_neo4j_map() for chunk in self.consists_of]
        })
        return map

@dataclass
class DocumentFilter:
    ids: Set[str] = None
    integrations: Set[str] = None

@dataclass
class ChunkFilter:
    ids: Set[str] = None
    types: Set[str] = None

@dataclass
class ProperNounFilter:
    ids: Set[str] = None
    types: Set[str] = None

@dataclass
class QueryFilter():
    user: str
    document_filter: DocumentFilter
    chunk_filter: ChunkFilter
    propernoun_filter: ProperNounFilter
    #TODO add edge filters