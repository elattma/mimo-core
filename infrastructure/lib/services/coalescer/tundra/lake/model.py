from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from util.model import Batch


class Drop:
    _batch: Batch
    _id: str
    _name: str
    _time: datetime

    def __init__(self, batch: Batch, name: str, datetime: datetime):
        self._batch = batch
        self._id = str(uuid4())
        self._name = name
        self._datetime = datetime

    def __repr__(self):
        return f'Drop(batch={self._batch}, id={self._id}, name={self._name}, _datetime={self._datetime})'

    def key(self):
        return f'{self._name}/{self._batch._section_type}/{self._datetime.year}/{self._datetime.month}/{self._datetime.day}/{self._datetime.hour}/{self._id}'

    def __eq__(self, other):
        if isinstance(other, Drop):
            return (
                self._id == other._id
                and self._name == other._name
                and self._datetime == other._datetime
            )
        return False

    def __hash__(self):
        return hash((self._id, self._name, self._datetime))
    
@dataclass
class PourResult:
    succeeded: bool
    drop: Drop
    error: str
