from abc import ABC
from dataclasses import dataclass
from typing import Any, List


@dataclass
class Access:
    id: str
    type: str

@dataclass
class Node(ABC):
    id: Any
    user: str

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

    def to_neo4j_map(self):
        map = super().to_neo4j_map()
        map.update({
            'integration': self.integration,
            'chunks': [chunk.target.to_neo4j_map() for chunk in self.consists_of]
        })
        return map
    