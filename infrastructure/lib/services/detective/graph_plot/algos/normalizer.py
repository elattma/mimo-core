from typing import Any, Dict, List, Set

from dstruct.model import (Block, Chunk, Property, StructuredProperty,
                           UnstructuredProperty)
from ulid import ulid


# TODO: experiment with using LLMs to normalize text or determine whether a property is structured
# TODO: normalize any timestamp or datetime object formats
class Normalizer:
    def __init__(self, max_chunk_len: int = 1000, chunk_overlap: int = 100) -> None:
        self._max_chunk_len = max_chunk_len
        self._chunk_overlap = chunk_overlap

    def _get_flattened(self, raw_dict: Dict[str, Any], accumulate_key: str = '') -> str:
        flattened = ''
        for key, value in raw_dict.items():
            if flattened:
                flattened += ', '

            if isinstance(value, dict):
                flattened += self._get_flattened(value, accumulate_key + key + '_')
            else:
                flattened += f'(key: {accumulate_key + key}, value: {value})'
        return flattened

    def _is_valid_value(self, value: Any) -> bool:
        if value is None:
            return False
        elif value == "":
            return False
        elif value == []:
            return False
        elif value == {}:
            return False
        elif value == "null":
            return False
        elif value == "None":
            return False
        elif value == "[]":
            return False
        elif value == "{}":
            return False
        elif value == " ":
            return False
        else:
            return True

    def _to_structured_property(self, key: str, value: Any) -> StructuredProperty:
        return StructuredProperty(key=key, value=value)

    def _to_unstructured_property(self, block_id: str, key: str, value: str) -> UnstructuredProperty:
        value_len = len(value)
        if value_len <= self._max_chunk_len:
            return UnstructuredProperty(key=key, chunks=[Chunk(
                ref_id=f'{block_id}#0',
                order=0,
                text=value,
                embedding=None
            )])
        
        min_chunkable = 1 + (value_len - self._chunk_overlap) // (self._max_chunk_len - self._chunk_overlap)
        chunks: List[Chunk] = []
        for i in range(0, min_chunkable):
            start = i * (self._max_chunk_len - self._chunk_overlap)
            end = min(start + self._max_chunk_len, value_len)
            chunks.append(Chunk(
                ref_id=f'{block_id}#{i}',
                order=i,
                text=value[start:end],
                embedding=None
            ))
        return UnstructuredProperty(key=key, chunks=chunks)

    def sanitize(self, dictionary: Dict[str, Any]) -> None:
        for key in list(dictionary):
            if key.startswith('_'):
                del dictionary[key]
                continue
            value = dictionary[key]
            if isinstance(value, dict):
                self.sanitize(value)
            if not self._is_valid_value(value):
                del dictionary[key]

    def with_properties(self, block: Block, dictionary: Dict[str, Any]) -> None:
        properties = set()
        for key, value in dictionary.items():
            property = None
            if isinstance(value, dict):
                flattened = self._get_flattened(value)
                property = self._to_unstructured_property(block_id=block.id, key=key, value=flattened)
            elif isinstance(value, (int, float)):
                property = self._to_structured_property(key=key, value=value)
            elif isinstance(value, list):
                list_str = str(value)
                property = self._to_unstructured_property(block_id=block.id, key=key, value=list_str)
            elif isinstance(value, str):
                property = self._to_unstructured_property(block_id=block.id, key=key, value=value)
            
            if not property:
                print(f'Unknown type: {type(value)} for value: {value}')
                continue
            properties.add(property)

        block.properties = properties
    
    def find_last_updated_timestamp(self, dictionary: Dict[str, Any]) -> int:
        # TODO: implement
        return 0
