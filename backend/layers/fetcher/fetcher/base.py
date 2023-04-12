from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Generator, List

from graph.blocks import Block, BlockStream

from .auth.base import Auth

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

@dataclass
class DiscoveryResponse:
    integration: str
    icon: str
    items: List[Item]
    next_token: str

class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}

    # TODO: add last sync time to filter only updated documents

    @classmethod
    def create(cls, integration, auth_params: dict, **kwargs):
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }

        if not integration or not cls.subclasses.get(integration, None):
            print(f'integration auth not found for {integration}')
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
        return f'assets.mimo.team/icons/{self._INTEGRATION}.svg'

    @abstractmethod
    def get_auth_type(self) -> str:
        raise NotImplementedError('get_auth_type not implemented')

    @abstractmethod
    def get_auth_attributes(self) -> dict:
        raise NotImplementedError('get_auth_attributes not implemented')

    @abstractmethod
    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        raise NotImplementedError('discover not implemented')

    @abstractmethod
    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        raise NotImplementedError("fetch not implemented")

    def _get_timestamp_from_format(self, timestamp_str: str, format: str = None) -> int:
        if not (timestamp_str and format):
            return None
        timestamp_datetime = datetime.strptime(timestamp_str, format)
        return int(timestamp_datetime.timestamp())

    def _streamify_blocks(self, label: str, blocks: List[Block]) -> List[BlockStream]:
        if not blocks or len(blocks) < 1:
            return []
        final_blocks: List[BlockStream] = []
        temporary_blocks: List[Block] = []
        total_blocks_size = 0
        for block in blocks:
            if not block:
                continue
            block_size = len(str(block))
            if block_size < 1:
                continue

            if total_blocks_size + block_size >= MAX_BLOCK_SIZE:
                if len(temporary_blocks) > 0:
                    final_blocks.append(BlockStream(label, temporary_blocks))
                    while total_blocks_size > MAX_BLOCK_OVERLAP or (
                        total_blocks_size + block_size > MAX_BLOCK_SIZE
                        and total_blocks_size > 0
                    ):
                        total_blocks_size -= len(str(temporary_blocks[0]))
                        temporary_blocks.pop(0)

            temporary_blocks.append(block)
            total_blocks_size += block_size
            
        if len(temporary_blocks) > 0:
            final_blocks.append(BlockStream(label, temporary_blocks))

        return final_blocks
