from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set


@dataclass
class Block:
    label: str
    last_updated_timestamp: int
    properties: Dict[str, Any] = None
    unstructured: str = None
    translated: str = None

    def __hash__(self) -> int:
        return hash((self.last_updated_timestamp, self.label, self.properties, self.unstructured))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.last_updated_timestamp == other.last_updated_timestamp and \
            self.label == other.label and \
            self.properties == other.properties and \
            self.unstructured == other.unstructured

    def as_dict(self) -> dict:
        return {
            'last_updated_timestamp': self.last_updated_timestamp,
            'label': self.label,
            'properties': self.properties,
            'unstructured': self.unstructured,
        }
    
    def is_valid(self) -> bool:
        return self.label and self.last_updated_timestamp and (self.properties or self.unstructured) and self.translated


@dataclass
class Entity:
    id: str = None
    value: str = None
    roles: List[str] = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.id == other.id

    def as_dict(self) -> dict:
        return {
            'id': self.id,
            'value': self.value,
            'roles': self.roles
        }


@dataclass
class Discovery:
    id: str
    type: str
    blocks: Set[Block] = None
    entities: Set[Entity] = None
    summary: str = None

    def add_blocks(self, blocks: List[Block]):
        if not blocks:
            return
        
        if not self.blocks:
            self.blocks = set()
        for block in blocks:
            if block.properties or block.unstructured:
                self.blocks.add(block)

    def add_entities(self, entities: List[Entity]):
        if not entities:
            return

        if not self.entities:
            self.entities = set()
        for entity in entities:
            if entity.id or entity.value:
                self.entities.add(entity)

    def is_valid(self) -> bool:
        return self.id and self.type and self.blocks and self.entities and self.summary
    
    def as_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'blocks': [block.as_dict() for block in self.blocks] if self.blocks else None,
            'entities': [entity.as_dict() for entity in self.entities] if self.entities else None,
            'summary': self.summary
        }

class Metric(Enum):
    TOTAL = 'total'
    SUCCEEDED = 'succeeded'
    FLUSHED = 'flushed'
    RETRIED = 'retried'
    FAILED = 'failed'

class Stats:
    def __init__(self) -> None:
        self._metrics: Dict[Metric, int] = {}

    def tally(self, metric: Metric, count: int):
        if not metric in self._metrics:
            self._metrics[metric] = 0
        self._metrics[metric] += count

    def as_dict(self):
        return {metric.value: count for metric, count in self._metrics.items()}