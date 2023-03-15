from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

from app.auth.base import Auth

MAX_CHUNK_SIZE = 600
MAX_CHUNK_OVERLAP = 50

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
class Chunk:
    content: str
    id: str = None
    title: str = None

@dataclass
class FetchResponse:
    integration: str
    chunks: List[Chunk]
    next_token: str = None

class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}

    # TODO: add last sync time to filter only updated documents

    @classmethod
    def create(cls, integration, auth_params: dict, **kwargs):
        if not cls.subclasses:
            cls.subclasses = {subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()}

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
    def fetch(self, id: str) -> FetchResponse:
        raise NotImplementedError('fetch not implemented')

    def __merge_chunks(self, chunks: List[Chunk]) -> Chunk:
        return Chunk(
            content='\n\n'.join([chunk.content for chunk in chunks]).strip()
        )

    def merge_split_chunks(self, chunks: List[Chunk]) -> List[Chunk]:
        if not chunks or len(chunks) < 1:
            return None
        final_chunks: List[Chunk] = []
        temporary_chunks: List[Chunk] = []
        total_chunks_size = 0
        for chunk in chunks:
            if not chunk or not chunk.content:
                continue
            chunk_size = len(chunk.content)
            if chunk_size < 1:
                continue
            
            if total_chunks_size + chunk_size >= MAX_CHUNK_SIZE:
                if total_chunks_size > MAX_CHUNK_SIZE:
                    print(f'Created a chunk of size {total_chunks_size}')
                
                if len(temporary_chunks) > 0:
                    final_chunks.append(self.__merge_chunks(temporary_chunks))
                    while total_chunks_size > MAX_CHUNK_OVERLAP or (total_chunks_size + chunk_size > MAX_CHUNK_SIZE and total_chunks_size > 0):
                        total_chunks_size -= len(temporary_chunks[0].content)
                        temporary_chunks.pop(0)
            
            temporary_chunks.append(chunk)
            total_chunks_size += chunk_size
        
        if len(temporary_chunks) > 0:
            final_chunks.append(self.__merge_chunks(temporary_chunks))
        
        return final_chunks
