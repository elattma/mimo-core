from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Block(ABC):
    _LABEL = 'block'
    last_updated_timestamp: int
    
    @abstractmethod
    def to_str(self) -> str:
        raise NotImplementedError('to_str not implemented')
    
    @abstractmethod
    def get_as_dict(self) -> dict:
        raise NotImplementedError('get_as_dict not implemented')

class BlockStream:
    blocks: List[Block]
    label: str

    def __init__(self, label: str, blocks: List[Block] = []):
        self.label = label
        self.blocks = blocks

    def add_block(self, block: Block):
        self.blocks.append(block)

    def to_str(self) -> str:
        return '\n\n'.join([block.to_str() for block in self.blocks])
    
    def get_as_dict(self) -> dict:
        return {
            'blocks': [block.get_as_dict() for block in self.blocks]
        }

@dataclass
class SummaryBlock(Block):
    _LABEL = 'summary'
    summary: str

    def to_str(self) -> str:
        return self.summary
    
    def get_as_dict(self) -> dict:
        return {
            'summary': self.summary
        }

@dataclass
class BodyBlock(Block):
    _LABEL = 'body'
    body: str

    def to_str(self) -> str:
        return self.body
    
    def get_as_dict(self) -> dict:
        return {
            'body': self.body
        }

@dataclass
class TitleBlock(Block):
    _LABEL = 'title'
    title: str

    def to_str(self) -> str:
        return self.title
    
    def get_as_dict(self) -> dict:
        return {
            'title': self.title
        }

# TODO: change to 1 block for all comments, but they have a chunkify method
@dataclass
class CommentBlock(Block):
    _LABEL = 'comment'
    author: str
    text: str

    def to_str(self) -> str:
        return f'{self.author}:{self.text}'
    
    def get_as_dict(self) -> dict:
        return {
            'author': self.author,
            'text': self.text
        }

@dataclass
class DealBlock(Block):
    _LABEL = 'deal'
    owner: str
    name: str
    contact: str
    type: str
    stage: str
    close_date: str
    amount: int
    probability: int

    def to_str(self) -> str:
        return ';'.join([f'{k}:{v}' for k, v in self.get_as_dict().items()])
    
    def get_as_dict(self) -> dict:
        return {
            'owner': self.owner,
            'name': self.name,
            'contact': self.contact,
            'type': self.type,
            'stage': self.stage,
            'close_date': self.close_date,
            'amount': self.amount,
            'probability': self.probability
        }

@dataclass
class ContactBlock(Block):
    _LABEL = 'contact'
    name: str
    created_by: str
    department: str
    title: str
    lead_source: str

    def to_str(self) -> str:
        return ';'.join([f'{k}:{v}' for k, v in self.get_as_dict().items()])
    
    def get_as_dict(self) -> dict:
        return {
            'name': self.name,
            'created_by': self.created_by,
            'department': self.department,
            'title': self.title,
            'lead_source': self.lead_source
        }