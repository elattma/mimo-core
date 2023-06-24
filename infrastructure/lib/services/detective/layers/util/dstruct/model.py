from abc import ABC
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, List, Literal, Optional, Set

from pydantic import BaseModel, Field


class Property(ABC):
    key: str

    def __hash__(self) -> int:
        return hash(self.key)
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.key == other.key

class StructuredProperty(Property):
    def __init__(self, key: str, value: Any) -> None:
        if not (key and value):
            raise ValueError('key and value are required')
        self.key = key
        self.value = value

@dataclass
class Chunk:
    ref_id: str
    order: int
    text: str
    embedding: List[float]

class UnstructuredProperty(Property):
    def __init__(self, key: str, chunks: Optional[List[Chunk]]) -> None:
        if not (key and chunks):
            raise ValueError('key is required')
        self.key = key
        self.chunks = chunks

@dataclass
class Block:
    id: str
    label: str
    integration: str
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
    
class BlockQuery(BaseModel):
    @property
    def current_date():
        return str(datetime.today().strftime('%Y-%m-%d'))
    
    @property
    def last_week_date():
        return str((datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    
    search_method: Literal['exact', 'relevant'] = Field(description=(
        'Determine whether the Request is looking for exact information '
        'or the most relevant information.'))
    concepts: Optional[str] = Field(description=(
        'Concepts that are semantically important. These capture '
        'whole ideas. For example, if the request is "Documents '
        'about the role of tech in the office", the concepts are '
        '"role of tech in the office"'
    ))
    entities: Optional[List[str]] = Field(description=(
        'A list of names of people. For example, '
        'if "The subjects of my last 5 emails from Troy Wilkerson", '
        'the entities should be ["Troy Wilkerson"]. You must be absolutely '
        'certain that they are a person!'
    ))
    absolute_time: Optional[str] = Field(description=(
        f'Specific timeframe requested. Today is {current_date}. '
        'For example, if "last week", then it should be '
        f'{last_week_date}. If Q2 2021, then '
        'it should be 2021-04-01.'
    ))
    relative_time_ascending: Optional[Literal['ASC', 'DESC']] = Field(description=(
        'Relative ordering of time like a SQL ASC statement. '
        'For example, if "most recent", '
        'then it should be DESC. If "first email" it should be ASC.'
    ))
    limit: Optional[int] = Field(description=(
        'Number of blocks to get. For example, if "most recent", '
        'then it should be 1. If "3 emails" it should be 3.'
    ))
    offset: Optional[int] = Field(description=(
        'Number of blocks to skip. For example, if "most recent", '
        'then it should be 0. If "second to last email" it should be 1.'
    ))
    labels: Optional[List[str]] = Field(description=(
        'Blocks are categorized into different types. Choose from the following block labels: '
    ))

    ids: Optional[List[str]]
    integrations: Optional[List[str]]
    embedding: Optional[List[float]]