from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List

MAX_CHUNK_SIZE = 2000
MAX_CHUNK_OVERLAP = 200

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
    next_token: str

class Fetcher(ABC):
    def __init__(self, access_token: str) -> None:
        super().__init__()
        self.access_token = access_token

    @abstractmethod
    def discover(self, filter: Any = None) -> DiscoveryResponse:
        pass

    @abstractmethod
    def fetch(self, id: str) -> FetchResponse:
        pass

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