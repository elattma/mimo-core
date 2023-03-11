from typing import List

import pinecone
from app.graph.blocks import Document


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
                    'indexed': ['user', 'documentId']
                }
            )
            self.index = pinecone.Index(index_name=index_name)
        
    def _delete_old_vectors(self, user: str, document_ids: List[str]) -> bool:
        if not (self.index and user and document_ids and len(document_ids) > 0):
            return False
        delete_response = self.index.delete(
            filter={
                'user': user,
                'documentId': {
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

    def upsert(self, documents: List[Document], user: str, timestamp: str):
        if not (self.index and user and documents and len(documents) > 0):
            return None
        vectors = []
        for document in documents:
            for consists_of in document.consists_of:
                vectors.append({
                    'id': consists_of.target.id,
                    'values': consists_of.target.embedding,
                    'metadata': {
                        'user': user,
                        'documentId': document.id,
                        'timestamp': timestamp
                    }
                })
        
        deleted = self._delete_old_vectors(user=user, document_ids=[document.id for document in documents])
        upserted = self._batched_upsert(vectors=vectors)
        return upserted and deleted
    
    def query(self, embedding: List[float], user: str, k: int = 5):
        if not (self.index and embedding and len(embedding) > 0):
            return None
        query_response = self.index.query(
            vector=embedding,
            top_k=k,
            filter={
                'user': user,
            },
            include_metadata=True,
            include_values=True
        )

        print(query_response)
        return query_response