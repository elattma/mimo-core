from dataclasses import dataclass
from enum import Enum
from typing import List

import pinecone
from app.graph.blocks import Document


class RowType(Enum):
    CHUNK = 'chunk'
    TRIPLET = 'triplet'

@dataclass
class Row:
    id: str
    embedding: List[float]
    owner: str
    document_id: str
    type: RowType


class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str = 'pre-alpha'):
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self.index = pinecone.Index(index_name=index_name)
        else:
            pinecone.create_index(
                name=index_name, 
                dimension=1536, 
                metadata_config={
                    'indexed': ['owner', 'document_id', 'type']
                }
            )
            self.index = pinecone.Index(index_name=index_name)
        
    def _delete_old_vectors(self, owners: List[str], document_ids: List[str]) -> bool:
        if not (self.index and owners and len(owners) > 0 and document_ids and len(document_ids) > 0):
            return False
        delete_response = self.index.delete(
            filter={
                'owner': {
                    '$in': owners
                },
                'document_id': {
                    '$in': document_ids
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
            upsert_response = self.index.upsert(vectors=vectors[batch_index:batch_index + batch_size])
            print(upsert_response)
            if hasattr(upsert_response, 'upserted_count') and upsert_response.upserted_count >= min(len_vectors - batch_index, batch_size):
                print(upsert_response.upserted_count)
            else:
                return False
        return True

    def upsert(self, rows: List[Row]):
        if not (self.index and rows and len(rows) > 0):
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
                'metadata': {
                    'owner': row.owner,
                    'document_id': row.document_id,
                    'type': row.type.value,
                }
            })
        
        deleted = self._delete_old_vectors(owners=list(owners), document_ids=list(document_ids))
        upserted = self._batched_upsert(vectors=vectors)
        return deleted and upserted
    
    def query(self, embedding: List[float], owner: str, k: int = 5):
        if not (self.index and embedding and len(embedding) > 0):
            return None
        query_response = self.index.query(
            vector=embedding,
            top_k=k,
            filter={
                'owner': owner,
            },
            include_metadata=True,
            include_values=True
        )

        print(query_response)
        return query_response