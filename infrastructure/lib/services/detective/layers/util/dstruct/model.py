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
        if key is None or value is None:
            raise ValueError('key and value are required')
        self.key = key
        self.value = value

@dataclass
class Chunk:
    order: int
    text: str
    embedding: List[float]

class UnstructuredProperty(Property):
    def __init__(self, key: str, chunks: Optional[List[Chunk]]) -> None:
        if key is None or chunks is None or len(chunks) == 0:
            raise ValueError('key and chunks are required')
        self.key = key
        self.chunks = chunks

@dataclass
class Block:
    id: str
    label: str
    integration: str
    connection: str
    properties: Set[Property]
    last_updated_timestamp: int
    embedding: List[float]
    
    def get_unstructured_properties(self) -> List[UnstructuredProperty]:
        return [property for property in self.properties if isinstance(property, UnstructuredProperty)]
    
    def get_structured_properties(self) -> List[StructuredProperty]:
        return [property for property in self.properties if isinstance(property, StructuredProperty)]
    
@dataclass
class Entity:
    identifiables: Set[str]
    name: str
    
SearchMethod = Literal['exact', 'relevant']
RelativeTime = Literal['asc', 'desc']
    
class BlockQuery(BaseModel):
    @property
    def current_date():
        return str(datetime.today().strftime('%Y-%m-%d'))
    
    @property
    def last_week_date_start():
        return str((datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    
    @property
    def last_week_date_end():
        return str((datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d'))
    
    search_method: Optional[SearchMethod] = Field(description=(
        'Determine whether the Request is looking for exact information '
        'or the most relevant information.'))
    concepts: Optional[str] = Field(description=(
        'Concepts that are semantically important. These capture '
        'whole ideas. For example, if the request is "Documents '
        'about the role of tech in the office", the concepts are '
        '"role of tech in the office"'
    ))
    # TODO: add the exact relation between these entities and the blocks
    entities: Optional[List[str]] = Field(description=(
        'A list of names of people or organizational things. For example, '
        'if "The subjects of my last 5 emails from Troy Wilkerson", '
        'the entities should be ["Troy Wilkerson"]. If given a question like "'
        'tell me more about Truhlar and Truhlar", the entities should be '
        '["Truhlar and Truhlar"]. '
    ))
    absolute_time_start: Optional[str] = Field(description=(
        'Datetime representing the beginning of the requested time range. '
        f'For reference, today is {current_date}. For example, if "last week", '
        f'then it should be {last_week_date_start}. If Q2 2021, then '
        'it should be 2021-04-01.'
    ))
    absolute_time_end: Optional[str] = Field(description=(
        'Datetime representing the end of the requested time range. '
        f'For reference, today is {current_date}. For example, if "last '
        f'week" then it should be {last_week_date_end}. If "Q2 2021", then '
        'it should be 2021-06-30.'
    ))
    relative_time: Optional[RelativeTime] = Field(description=(
        'Relative ordering of time like a SQL ASC statement. '
        'For example, if "most recent", '
        'then it should be DESC. If "first email" it should be ASC.'
    ))
    limit: Optional[int] = Field(description=(
        'Number of blocks to get. For example, if "most recent", '
        'then it should be 1. If "3 emails" it should be 3. '
        'This must be explicitly mentioned!'
    ))
    offset: Optional[int] = Field(description=(
        'Number of blocks to skip. For example, if "most recent", '
        'then it should be 0. If "second to last email" it should be 1.'
    ))
    labels: Optional[List[str]] = Field(description=(
        'A label denotes the set of information contained in a block. '
        'For example, when the user refers to "emails related to", the list of labels should be '
        '["email_thread"]. When the user refers to "notes about", the labels should be '
        '["document", "note", "website"]. When you are not absolutely certain, include '
        'any labels that could possibly be related. Be very lenient! If you\'re not sure, '
        'do not guess and you must leave this field empty!'
    ))

    ids: Optional[List[str]]
    integrations: Optional[List[str]]
    embedding: Optional[List[float]]

    def __str__(self) -> str:
        return (
            '{ search_method: ' + str(self.search_method if self.search_method else 'empty') + ', '
            'concepts: ' + str(self.concepts if self.concepts else 'empty') + ', '
            'entities: ' + str(self.entities if self.entities else 'empty') + ', '
            'absolute_time_start: ' + str(self.absolute_time_start if self.absolute_time_start else 'empty') + ', '
            'absolute_time_end: ' + str(self.absolute_time_end if self.absolute_time_end else 'empty') + ', '
            'relative_time: ' + str(self.relative_time if self.relative_time else 'empty') + ', '
            'limit: ' + str(self.limit if self.limit else 'empty') + ', '
            'offset: ' + str(self.offset if self.offset else 'empty') + ', '
            'labels: ' + str(self.labels if self.labels else 'empty') + ', '
            'ids: ' + str(self.ids if self.ids else 'empty') + ', '
            'integrations: ' + str(self.integrations if self.integrations else 'empty') + ', '
            'embedding: ' + ('exists' if self.embedding else 'dne') + ' }'
        )
