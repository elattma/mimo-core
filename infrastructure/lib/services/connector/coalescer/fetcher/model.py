from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict

MAX_UNSTRUCTURED_SIZE = 1000


def get_timestamp_from_format(timestamp_str: str, format: str = None) -> int:
    if not (timestamp_str and format):
        return None
    timestamp_datetime = datetime.strptime(timestamp_str, format)
    return int(timestamp_datetime.timestamp())

@dataclass
class Filter:
    start_timestamp: int = None
    limit: int = None

class StreamData:
    def __init__(self, name: str, id: str) -> None:
        self._name = name
        self._id = id
        self._data: Dict[str, Any] = {}
    
    def add_unstructured_data(self, key: str, value: str):
        if not (key and value):
            print(f'[add_unstructured_data] kv missing..')
            return
        if key not in self._data:
            self._data[key] = []
        unstructured_chunks = self._data[key]
        if type(unstructured_chunks) != list:
            print(f'[add_unstructured_data] error unstructured_chunks is not a list..')
            return
        last_chunk = unstructured_chunks.pop() if unstructured_chunks else ""
        last_chunk = last_chunk + value
        if len(last_chunk) > MAX_UNSTRUCTURED_SIZE:
            for i in range(0, len(last_chunk), MAX_UNSTRUCTURED_SIZE):
                unstructured_chunks.append(last_chunk[i:i+MAX_UNSTRUCTURED_SIZE])

        unstructured_chunks.append(value)

    def add_structured_data(self, key: str, value: Any):
        if not (key and value):
            print(f'[add_structured_data] kv missing..')
            return
        if key in self._data:
            print(f'[add_structured_data] key already exists..')
            return
        self._data[key] = value

    def add_structured_data_as_list(self, key: str, value: Any):
        if not (key and value):
            print(f'[add_structured_data_as_list] kv missing..')
            return
        if key not in self._data:
            self._data[key] = []
        list_data = self._data[key]
        if type(list_data) != list:
            print(f'[add_structured_data_as_list] error list_data is not a list..')
            return
        list_data.append(value)
