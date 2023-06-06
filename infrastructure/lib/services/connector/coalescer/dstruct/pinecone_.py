from dataclasses import dataclass
from typing import List

import pinecone


@dataclass
class Row:
    id: str
    embedding: List[float]
    library: str
    date_day: str
    block_label: str
    page_type: str

    def to_metadata_dict(self):
        return {
            'library': self.library,
            'date_day': self.date_day,
            'block_label': self.block_label,
            'page_type': self.page_type
        }


class Pinecone:
    def __init__(self, library: str, api_key: str, environment: str, index_name: str = 'beta'):
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        self._library = library
        if not (self._index and self._library):
            raise Exception('Pinecone index or library not found')
        
    def _with_library(self, id: str):
        return f'{self._library}#{id}'
    
    def _without_library(self, id: str):
        return id.split('#')[-1]

    def delete(self, ids: List[str]) -> bool:
        if not ids:
            return False

        delete_response = self._index.delete(ids=[self._with_library(id) for id in ids])
        print(f'[Pinecone] Delete response: {delete_response}')
        return True

    def _batched_upsert(self, vectors: List[dict], batch_size: int = 100) -> bool:
        if not vectors:
            return False

        len_vectors = len(vectors)
        for batch_index in range(0, len_vectors, batch_size):
            upsert_response = self._index.upsert(
                vectors=vectors[batch_index:batch_index + batch_size])
            print(f'[Pinecone] Upsert response: {upsert_response}')
            upserted = upsert_response.get('upserted_count', 0) if upsert_response else 0
            if hasattr(upsert_response, 'upserted_count') and upserted >= min(len_vectors - batch_index, batch_size):
                print(f'[Pinecone] Upsert response count: {upserted}')
            else:
                return False
        return True

    def upsert(self, rows: List[Row]):
        if not (self._index and rows and len(rows) > 0):
            return None
        vectors = []
        for row in rows:
            vectors.append({
                'id': self._with_library(row.id),
                'values': row.embedding,
                'metadata': row.to_metadata_dict()
            })

        return self._batched_upsert(vectors=vectors)

    def fetch(self, ids: List[str]):
        if not (self._index and ids and len(ids) > 0):
            return None

        fetch_response = self._index.fetch(ids=[self._with_library(id) for id in ids])
        return fetch_response.get('vectors', None) if fetch_response else None
