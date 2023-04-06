from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass
class Block(ABC):
    _LABEL = 'block'
    last_updated_timestamp: int
    
    def __str__(self) -> str:
        return ';'.join([f'{k}:{v}' for k, v in self.get_as_dict().items()])
    
    @abstractmethod
    def get_as_dict(self) -> dict:
        raise NotImplementedError('get_as_dict not implemented')

class BlockStream:
    blocks: List[Block]
    label: str

    def __init__(self, label: str, blocks: List[Block]):
        self.label = label
        self.blocks = [block for block in blocks]

    def __str__(self) -> str:
        return '\n\n'.join([str(block) for block in self.blocks])

    def get_as_dict(self) -> dict:
        return {
            'blocks': [block.get_as_dict() for block in self.blocks]
        }

@dataclass
class SummaryBlock(Block):
    _LABEL = 'summary'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }

@dataclass
class BodyBlock(Block):
    _LABEL = 'body'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }

class Relations(Enum):
    AUTHOR = 'author'
    RECIPIENT = 'recipient'
    PARTICIPANT = 'participant'

@dataclass
class entity:
    id: str
    value: str

    def __str__(self) -> str:
        return f'{self.id}:{self.value}'

    def __hash__(self) -> int:
        return hash(self.id)
    
    def get_as_dict(self) -> dict:
        return {
            'id': self.id,
            'value': self.value
        }

@dataclass
class MemberBlock(Block):
    _LABEL = 'member'
    name: entity
    relation: Relations
    
    def get_as_dict(self) -> dict:
        return {
            'name': self.name.get_as_dict(),
            'relation': self.relation.value
        }

@dataclass
class TitleBlock(Block):
    _LABEL = 'title'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }

# TODO: change to 1 block for all comments, but they have a chunkify method
@dataclass
class CommentBlock(Block):
    _LABEL = 'comment'
    author: entity
    text: str
    
    def get_as_dict(self) -> dict:
        return {
            'author': self.author.get_as_dict(),
            'text': self.text
        }

@dataclass
class DealBlock(Block):
    _LABEL = 'deal'
    owner: entity
    name: entity
    contact: entity
    type: str
    stage: str
    close_date: str
    amount: int
    probability: int
    
    def get_as_dict(self) -> dict:
        return {
            'owner': self.owner.get_as_dict(),
            'name': self.name.get_as_dict(),
            'contact': self.contact.get_as_dict(),
            'type': self.type,
            'stage': self.stage,
            'close_date': self.close_date,
            'amount': self.amount,
            'probability': self.probability
        }

@dataclass
class ContactBlock(Block):
    _LABEL = 'contact'
    name: entity
    created_by: entity
    department: str
    title: str
    lead_source: str

    def get_as_dict(self) -> dict:
        return {
            'name': self.name.get_as_dict(),
            'created_by': self.created_by.get_as_dict(),
            'department': self.department,
            'title': self.title,
            'lead_source': self.lead_source
        }