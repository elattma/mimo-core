from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List

from app.auth.base import Auth

MAX_BLOCK_SIZE = 600
MAX_BLOCK_OVERLAP = 50

# TODO: add last sync time to filter only updated documents
@dataclass
class Filter:
    next_token: str = None
    limit: int = 20

@dataclass
class Item:
    id: str
    title: str
    link: str
    preview: str

@dataclass
class DiscoveryResponse:
    integration: str
    icon: str
    items: List[Item]
    next_token: str


@dataclass
class Block(ABC):
    _LABEL = 'base'
    subclasses = {}

    @abstractmethod
    def to_str(self) -> str:
        raise NotImplementedError('to_str not implemented')
    
    @abstractmethod
    def get_as_dict(self) -> dict:
        raise NotImplementedError('get_as_dict not implemented')

class BlockStream:
    blocks: List[Block]

    def __init__(self, blocks: List[Block] = []):
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

class Fetcher(ABC):
    _INTEGRATION = "base"

    subclasses = {}

    # TODO: add last sync time to filter only updated documents

    @classmethod
    def create(cls, integration, auth_params: dict, **kwargs):
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }

        if not integration or not cls.subclasses.get(integration, None):
            print(f"integration auth not found for {integration}")
            return None

        fetcher = cls.subclasses[integration]()
        fetcher_auth_overrides = fetcher.get_auth_attributes()
        if fetcher_auth_overrides:
            auth_params.update(fetcher_auth_overrides)
        fetcher.define_auth(fetcher.get_auth_type(), **auth_params)
        fetcher.init(**kwargs)

        return fetcher

    def init(self, last_fetch_timestamp: int = None):
        self.last_fetch_timestamp = last_fetch_timestamp

    def define_auth(self, auth_type: str, **kwargs):
        self.auth = Auth.create(auth_type, **kwargs)
        self.auth.validate()

    def get_icon(self) -> str:
        return f"assets.mimo.team/icons/{self._INTEGRATION}.svg"

    @abstractmethod
    def get_auth_type(self) -> str:
        raise NotImplementedError("get_auth_type not implemented")

    @abstractmethod
    def get_auth_attributes(self) -> dict:
        raise NotImplementedError("get_auth_attributes not implemented")

    @abstractmethod
    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        raise NotImplementedError("discover not implemented")

    @abstractmethod
    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        raise NotImplementedError("fetch not implemented")

    def _streamify_blocks(self, blocks: List[Block]) -> List[BlockStream]:
        if not blocks or len(blocks) < 1:
            return []
        final_blocks: List[BlockStream] = []
        temporary_blocks: List[Block] = []
        total_blocks_size = 0
        for block in blocks:
            if not block:
                continue
            block_size = len(block.to_str())
            if block_size < 1:
                continue

            if total_blocks_size + block_size >= MAX_BLOCK_SIZE:
                if total_blocks_size > MAX_BLOCK_SIZE:
                    print(f'Created a block of size {total_blocks_size}')

                if len(temporary_blocks) > 0:
                    final_blocks.append(BlockStream(temporary_blocks))
                    while total_blocks_size > MAX_BLOCK_OVERLAP or (
                        total_blocks_size + block_size > MAX_BLOCK_SIZE
                        and total_blocks_size > 0
                    ):
                        total_blocks_size -= len(temporary_blocks[0])
                        temporary_blocks.pop(0)

            temporary_blocks.append(block)
            total_blocks_size += block_size
            
        if len(temporary_blocks) > 0:
            final_blocks.append(BlockStream(temporary_blocks))

        return final_blocks
