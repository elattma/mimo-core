from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Set


class Property(ABC):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key == other.key

    @abstractmethod
    def as_dict(self) -> Dict[str, Any]:
        raise NotImplementedError

class StructuredProperty(Property):
    def __init__(self, key: str, value: Any) -> None:
        # TODO: add validation
        self.key = key
        self.value = value

@dataclass
class Chunk:
    ref_id: str
    order: int
    text: str
    embedding: List[float]

class UnstructuredProperty(Property):
    def __init__(self, key: str, chunks: List[Chunk]) -> None:
        # TODO: add validation
        self.key = key
        self.chunks = chunks

@dataclass
class Block:
    id: str
    label: str
    properties: Set[Property]
    last_updated_timestamp: int
    embedding: List[float]

    def __hash__(self) -> int:
        return hash((self.id, self.label))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id and self.label == other.label
    
    def get_unstructured_properties(self) -> List[UnstructuredProperty]:
        return [property for property in self.properties if isinstance(property, UnstructuredProperty)]
    
    def get_structured_properties(self) -> List[StructuredProperty]:
        return [property for property in self.properties if isinstance(property, StructuredProperty)]
    
    def is_valid(self) -> bool:
        return self.id and self.label and self.properties and self.last_updated_timestamp and self.embedding
    
@dataclass
class Entity:
    id: str
    identifiables: Set[str]
    value: str

    def __hash__(self) -> int:
        return hash((self.value))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.value == other.value