from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Set

from ulid import ulid


class Block:
    def __init__(self, label: str, properties: Dict[str, Any], last_updated_timestamp: int) -> None:
        self._id = ulid()
        self._label = label
        self._properties = properties
        self._last_updated_timestamp = last_updated_timestamp

    def __hash__(self) -> int:
        return hash((self._label, str(self._properties), self._last_updated_timestamp))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._label == other._label and \
            self._properties == other._properties and \
            self._last_updated_timestamp == other._last_updated_timestamp 

    def as_dict(self) -> dict:
        return {
            'id': self._id,
            'label': self._label,
            'properties': self._properties,
            'last_updated_timestamp': self._last_updated_timestamp,
        }
    
    def is_valid(self) -> bool:
        return self._id and self._label and self._properties and self._last_updated_timestamp 


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