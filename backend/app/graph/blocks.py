from abc import ABC
from dataclasses import dataclass
from typing import Any, List


@dataclass
class Access:
    id: str
    type: str

@dataclass
class Embedding:
    embedding: List[float]

@dataclass
class Node(ABC):
    id: Any
    timestamp: int

    def to_neo4j_map(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
        }

@dataclass
class Edge(ABC):
    type: str
    target: Node
 
@dataclass
class ProperNoun(Node):
    type: str

    def to_neo4j_map(self):
        return super().to_neo4j_map().update({
            'type': type
        })

@dataclass
class REFERENCES(Edge):
    type = 'REFERENCES'
    target = ProperNoun

@dataclass
class Chunk(Node):
    content: str
    type: str
    references: List[REFERENCES]

    def to_neo4j_map(self):
        return super().to_neo4j_map().update({
            'content': self.content,
            'type': self.type,
            'propernouns': [ref.target.to_neo4j_map() for ref in self.references]
        })

class CONSISTS_OF(Edge):
    type = 'CONSISTS_OF'
    target = Chunk

@dataclass
class Document(Node):
    integration: str
    consists_of: List[CONSISTS_OF]

    def to_neo4j_map(self):
        return super().to_neo4j_map().update({
            'integration': self.integration,
            'chunks': [chunk.target.to_neo4j_map() for chunk in self.consists_of]
        })
    