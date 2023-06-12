import json
from dataclasses import dataclass
from typing import Literal, Set

UNIQUE_PATTERN_MIMO_PLACEHOLDER = '<UNQIUE_PLACEHOLDER>'

@dataclass
class SemanticFilter:
    library: str
    min_date_day: int = None
    max_date_day: int = None
    page_type: set[str] = None
    page_id: set[str] = None
    block_label: set[str] = None

    def to_dict(self):
        filter = {
            'library': self.library
        }
        if self.min_date_day or self.max_date_day:
            date_day = {}
            if self.min_date_day:
                date_day['$gte'] = self.min_date_day
            if self.max_date_day:
                date_day['$lte'] = self.max_date_day

            filter['date_day'] = date_day
        if self.page_type:
            filter['page_type'] = {
                '$or': list(self.page_type)
            }
        if self.page_id:
            filter['page_id'] = {
                '$in': list(self.page_id)
            }
        if self.block_label:
            filter['block_label'] = {
                '$in': list(self.block_label)
            }
        return filter
    
@dataclass
class GraphFilter:
    library: str
    page_filter: 'PageFilter' = None
    block_filter: 'BlockFilter' = None
    name_filter: 'NameFilter' = None
    order: 'Order' = None
    pagination: 'Pagination' = None

@dataclass
class PageFilter:
    id: Set[str] = None
    connection: Set[str] = None
    type: Set[str] = None
    time_range: tuple[int, int] = None

@dataclass
class BlockFilter:
    id: Set[str] = None
    label: Set[str] = None
    time_range: tuple[int, int] = None
    kv_match: Set['KeyValueMatch'] = None
    key_regex_match: Set['KeyRegexMatch'] = None

@dataclass
class NameFilter:
    id: Set[str] = None
    value: Set[str] = None
    role: Set[str] = None

@dataclass
class Order:
    direction: Literal['ASC', 'DESC']
    property: Literal['last_updated_timestamp']

@dataclass
class Pagination:
    offset: int
    count: int

@dataclass
class KeyValueMatch:
    key: str
    value: str

    def __hash__(self):
        return hash((self.key, self.value))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key == other.key and self.value == other.value

@dataclass
class KeyRegexMatch:
    key: str
    match: str
    label: str = None
    filter: str = None

    @staticmethod
    def from_dict(matcher_dict: dict, label: str = None, filter: str = None):
        KeyRegexMatch.replace_null_fields(matcher_dict)
        match = json.dumps(matcher_dict).replace(
            f'"{KeyRegexMatch.get_any_match_placeholder()}"', '"([^"]*)"'
        )
        return KeyRegexMatch(match=f'.*{match}.*', label=label, filter=filter)

    @staticmethod
    def from_contains(substring: str):
        return KeyRegexMatch(match=f'.*{substring}.*')

    @staticmethod
    def get_entity_id_match_placeholder():
        return '<ENTITY_ID_MATCH_PLACEHOLDER>'

    @staticmethod
    def get_any_match_placeholder():
        return '<ANY_MATCH_PLACEHOLDER>'

    @staticmethod
    def replace_null_fields(dictionary: dict):
        for key, value in dictionary.items():
            if not value:
                dictionary[key] = KeyRegexMatch.get_any_match_placeholder()
            elif isinstance(value, dict):
                KeyRegexMatch.replace_null_fields(value)

    def __hash__(self):
        return hash((self.label))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.label == other.label
