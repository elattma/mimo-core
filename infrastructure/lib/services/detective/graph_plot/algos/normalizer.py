import json
from datetime import datetime
from typing import Any, Dict, List

from dateutil import parser
from dstruct.model import (Block, Chunk, StructuredProperty,
                           UnstructuredProperty)


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
    
    def _casted(self, raw_dict: Dict[str, Any], key: str) -> None:
        value = raw_dict[key]
        if not value:
            return
        
        try:  # bool
            if value.lower() in ["true", "false"]:
                raw_dict[key] = bool(value.lower() == "true")
                return
        except ValueError:
            pass

        try:  # int
            raw_dict[key] = int(value)
            return
        except ValueError:
            pass

        try:  # float
            raw_dict[key] = float(value)
            return
        except ValueError:
            pass

        try:  # dict
            potential_dict = json.loads(value)
            if isinstance(potential_dict, dict):
                raw_dict[key] = potential_dict
                return
        except json.JSONDecodeError:
            pass

        try:  # datetime
            raw_dict[key] = parser.parse(value)
            return
        except ValueError:
            pass
        
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
        print(f'[Normalizer._to_structured_property] key: {key}, value: {value}')
        return StructuredProperty(key=key, value=value)

    def _to_unstructured_property(self, key: str, value: str) -> UnstructuredProperty:
        value_len = len(value)
        if value_len <= self._max_chunk_len:
            print(f'[Normalizer._to_unstructured_property] key: {key}, chunks: {value}')
            return UnstructuredProperty(key=key, chunks=[Chunk(
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
                order=i,
                text=value[start:end],
                embedding=None
            ))
        print(f'[Normalizer._to_unstructured_property] key: {key}, chunks: {chunks}')
        return UnstructuredProperty(key=key, chunks=chunks)

    def sanitize(self, dictionary: Dict[str, Any]) -> None:
        print(f'[Normalizer.sanitize] dictionary: {dictionary}')
        for key in list(dictionary):
            if key.startswith('_'):
                del dictionary[key]
                continue
            value = dictionary[key]
            self._casted(dictionary, key)
            if isinstance(value, dict):
                self.sanitize(value)
            if not self._is_valid_value(value):
                dictionary.pop(key, None)
        print(f'[Normalizer.sanitize] sanitized dictionary: {dictionary}')

    def with_properties(self, block: Block, dictionary: Dict[str, Any]) -> None:
        properties = set()
        for key, value in dictionary.items():
            property = None
            if isinstance(value, dict):
                flattened = self._get_flattened(value)
                property = self._to_unstructured_property(key=key, value=flattened)
            elif isinstance(value, (int, float)):
                property = self._to_structured_property(key=key, value=value)
            elif isinstance(value, list):
                list_str = str(value)
                property = self._to_unstructured_property(key=key, value=list_str)
            elif isinstance(value, str):
                property = self._to_unstructured_property(key=key, value=value)
            
            if not property:
                print(f'Unknown type: {type(value)} for value: {value}')
                continue
            properties.add(property)

        block.properties = properties
    
    def find_last_updated_ts(self, dictionary: Dict[str, Any]) -> int:
        dictionary_keys = dictionary.keys()

        potential_keys: List[str] = []
        for key in dictionary_keys:
            if 'last' in key and 'time' in key and isinstance(dictionary[key], datetime):
                potential_keys.append(key)

        if potential_keys:
            for potential_key in potential_keys:
                try:
                    dictionary_value: datetime = dictionary[potential_key]
                    timestamp: int = int(dictionary_value.timestamp())
                    return timestamp
                except Exception as e:
                    print(f'[Normalizer.find_last_updated_timestamp] Error parsing date: {e}')
                    continue

        # TODO: fallback with LLM call on keys
        return 0
