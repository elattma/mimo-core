from dataclasses import dataclass
from enum import Enum
from typing import List

import pinecone


class RowType(Enum):
    BLOCK = 'block'
    TRIPLET = 'triplet'

@dataclass
class Row:
    id: str
    embedding: List[float]

    owner: str
    type: RowType
    date_day: int

    integration: str
    document_id: str
    block_label: str

    def to_metadata_dict(self):
        return {
            'owner': self.owner,
            'type': self.type.value,
            'date_day': self.date_day,
            'integration': self.integration,
            'document_id': self.document_id,
            'block_label': self.block_label,
        }

@dataclass
class Filter:
    owner: str
    type: set[RowType] = None
    min_date_day: int = None
    max_date_day: int = None
    integration: set[str] = None
    document_id: set[str] = None
    block_label: set[str] = None

    def to_dict(self):
        filter = {
            'owner': self.owner
        }
        if self.type:
            filter['type'] = {
                '$in': [t.value for t in self.type]
            }
        if self.min_date_day or self.max_date_day:
            date_day = {}
            if self.min_date_day:
                date_day['$gte'] = self.min_date_day
            if self.max_date_day:
                date_day['$lte'] = self.max_date_day

            filter['date_day'] = date_day
        if self.integration:
            filter['integration'] = {
                '$in': list(self.integration)
            }
        if self.document_id:
            filter['document_id'] = {
                '$in': list(self.document_id)
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
            pinecone.create_index(
                name=index_name, 
                dimension=1536, 
                metadata_config={
                    'indexed': ['owner', 'type', 'date_day', 'integration', 'document_id', 'block_label']
                }
            )
            self._index = pinecone.Index(index_name=index_name)
        
    def _delete_old_vectors(self, rows: List[Row]) -> bool:
        if not (self._index and rows and len(rows) > 0):
            return False
        
        owners = set([row.owner for row in rows])
        document_ids = set([row.document_id for row in rows])

        delete_response = self._index.delete(
            filter={
                'owner': {
                    '$in': list(owners)
                },
                'document_id': {
                    '$in': list(document_ids)
                }
            }
        )
        print('delete response!')
        print(delete_response)

        return True

    def _batched_upsert(self, vectors: List[dict], batch_size: int = 100) -> bool:
        if not vectors or len(vectors) < 1:
            return False
        
        len_vectors = len(vectors)
        for batch_index in range(0, len_vectors, batch_size):
            upsert_response = self._index.upsert(vectors=vectors[batch_index:batch_index + batch_size])
            print(upsert_response)
            if hasattr(upsert_response, 'upserted_count') and upsert_response.upserted_count >= min(len_vectors - batch_index, batch_size):
                print(upsert_response.upserted_count)
            else:
                return False
        return True

    def upsert(self, rows: List[Row]):
        if not (self._index and rows and len(rows) > 0):
            return None
        vectors = []
        owners = set()
        document_ids = set()
        for row in rows:
            owners.add(row.owner)
            document_ids.add(row.document_id)

            vectors.append({
                'id': row.id,
                'values': row.embedding,
                'metadata': row.to_metadata_dict()
            })
            print(row.to_metadata_dict())
        
        deleted = self._delete_old_vectors(rows)
        upserted = self._batched_upsert(vectors=vectors)
        return deleted and upserted
    
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
        vectors = fetch_response.get('vectors', None) if fetch_response else None
        return vectors
