from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import pinecone


class RowType(Enum):
    BLOCK = 'block'
    TRIPLET = 'triplet'

@dataclass
class Row:
    id: str
    embedding: List[float]

    owner: str
    integration: str
    document_id: str
    type: RowType
    date_day: int

    def to_metadata_dict(self):
        return {
            'owner': self.owner,
            'integration': self.integration,
            'document_id': self.document_id,
            'type': self.type.value,
            'date_day': self.date_day
        }

@dataclass
class Filter:
    owner: str
    integration: set[str] = None
    document_id: set[str] = None
    type: set[RowType] = None
    min_max_date_day: Tuple[int, int] = None

    def to_dict(self):
        filter = {
            'owner': self.owner
        }
        if self.integration:
            filter['integration'] = {
                '$in': list(self.integration)
            }
        if self.document_id:
            filter['document_id'] = {
                '$in': list(self.document_id)
            }
        if self.type:
            filter['type'] = {
                '$in': [t.value for t in self.type]
            }
        if self.min_max_date_day:
            filter['date_day'] = {
                '$gte': self.min_max_date_day[0],
                '$lte': self.min_max_date_day[1]
            }
        return filter

class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str = 'pre-alpha'):
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        else:
            pinecone.create_index(
                name=index_name, 
                dimension=1536, 
                metadata_config={
                    'indexed': ['owner', 'integration', 'document_id', 'type']
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