from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set


@dataclass
class Block:
    label: str
    last_updated_timestamp: int
    properties: Dict[str, Any]

    def __hash__(self) -> int:
        return hash((self.last_updated_timestamp, self.label, self.properties))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.last_updated_timestamp == other.last_updated_timestamp and \
            self.label == other.label and \
            self.properties == other.properties

    def as_dict(self) -> dict:
        return {
            'last_updated_timestamp': self.last_updated_timestamp,
            'label': self.label,
            'properties': self.properties
        }
    
    def is_valid(self) -> bool:
        return self.label and self.last_updated_timestamp and self.properties


@dataclass
class Discovery:
    id: str
    type: str
    blocks: Set[Block] = None

    def add_blocks(self, blocks: List[Block]):
        if not blocks:
            return
        
        if not self.blocks:
            self.blocks = set()
        for block in blocks:
            if block.is_valid():
                self.blocks.add(block)

    def is_valid(self) -> bool:
        return self.id and self.type and self.blocks
    
    def as_dict(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'blocks': [block.as_dict() for block in self.blocks] if self.blocks else None
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