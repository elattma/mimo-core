import sys
from typing import Dict, Generator, List

from fetcher.base import Section

MAX_BYTES = 10 * 1000 * 1000

class Batch:
    _section_type: str
    _sections: List[Section]
    _size: int

    def __init__(self, section_type: str):
        self._section_type = section_type
        self._sections = []
        self._size = 0

    def table(self) -> str:
        return '\n'.join([section.row() for section in self._sections])

    def add(self, section: Section) -> int:
        if section.discovery.type() != self._section_type:
            raise ValueError('section type mismatch')
        self._sections.append(section)
        self._size += sys.getsizeof(section)
        return self._size

class Batcher:
    _batches: Dict[str, Batch]
    _max_bytes: int

    def __init__(self, max_bytes: int = MAX_BYTES):
        self._batches = {}
        self._max_bytes = max_bytes

    def add(self, sections: List[Section]) -> Generator[Batch, None, None]:
        for section in sections:
            section_type = section.discovery.type()
            if section_type not in self._batches:
                self._batches[section_type] = Batch(section_type)
            batch = self._batches[section_type]
            new_size = batch.add(section)
            if new_size > self._max_bytes:
                yield batch
                self._batches[section_type] = Batch(section_type)
    
    def flush(self) -> List[Batch]:
        return [batch for batch in self._batches.values() if batch._sections]