from dataclasses import dataclass
from enum import Enum
from typing import List

import pinecone
from graph.blocks import PageType


@dataclass
class RowType(Enum):
    BLOCK = 'block'
    PAGE = 'page'

@dataclass
class Row:
    id: str
    embedding: List[float]

    library: str
    row_type: RowType
    date_day: int

    page_types: List[PageType]
    connection: str
    block_label: str

    def to_metadata_dict(self):
        return {
            'library': self.library,
            'row_type': self.row_type.value,
            'date_day': self.date_day,
            'page_types': [page_type.value for page_type in self.page_types],
            'connection': self.connection,
            'block_label': self.block_label,
        }

@dataclass
class Filter:
    library: str
    row_type: set[RowType] = None
    min_date_day: int = None
    max_date_day: int = None
    page_types: set[PageType] = None
    connection: set[str] = None
    page_id: set[str] = None
    block_label: set[str] = None

    def to_dict(self):
        filter = {
            'library': self.library
        }
        if self.row_type:
            filter['row_type'] = {
                '$in': [t.value for t in self.row_type]
            }
        if self.min_date_day or self.max_date_day:
            date_day = {}
            if self.min_date_day:
                date_day['$gte'] = self.min_date_day
            if self.max_date_day:
                date_day['$lte'] = self.max_date_day

            filter['date_day'] = date_day
        if self.page_types:
            filter['page_types'] = {
                '$or': [{
                    '$in': type.value
                } for type in self.page_types]
            }
        if self.connection:
            filter['connection'] = {
                '$in': list(self.connection)
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


class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str = 'beta'):
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        else:
            raise Exception(f'Pinecone index {index_name} not found')

    def delete(self, page_ids: List[str], library: str) -> bool:
        if not (self._index and page_ids and library):
            return False

        delete_response = self._index.delete(
            filter={
                'library': {
                    '$in': [library]
                },
                'page_id': {
                    '$in': page_ids
                }
            }
        )
        print(f'[Pinecone] Delete response: {delete_response}')
        return True

    def _batched_upsert(self, vectors: List[dict], batch_size: int = 100) -> bool:
        if not vectors or len(vectors) < 1:
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
                'id': row.id,
                'values': row.embedding,
                'metadata': row.to_metadata_dict()
            })

        return self._batched_upsert(vectors=vectors)

    def query(self, embedding: List[float], query_filter: Filter, k: int = 5):
        if not (self._index and embedding and len(embedding) > 0):
            return None

        query_response = self._index.query(
            vector=embedding,
            top_k=k,
            filter=query_filter.to_dict(),
            include_metadata=True,
            include_values=True
        )

        return query_response.get('matches', None) if query_response else None

    def fetch(self, ids: List[str]):
        if not (self._index and ids and len(ids) > 0):
            return None

        fetch_response = self._index.fetch(ids=ids)
        return fetch_response.get('vectors', None) if fetch_response else None
