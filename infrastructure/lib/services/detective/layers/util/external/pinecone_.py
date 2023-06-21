from typing import List

import pinecone


class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str = 'beta'):
        print(f'[Pinecone.__init__] starting')
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        if not self._index:
            raise Exception('[Pinecone.__init__] index not found')
        print(f'[Pinecone.__init__] completed')
        
    def delete(self, ids: List[str]) -> bool:
        print(f'[Pinecone.delete] ids: {ids}')
        if not ids:
            return False

        delete_response = self._index.delete(ids)
        print(f'[Pinecone.delete] response: {delete_response}')
        return True

    def upsert(self, vectors: List[dict], batch_size: int = 100) -> bool:
        print('[Pinecone.upsert] vectors:', len(vectors) if vectors else 0, 'batch_size:', batch_size)
        if not vectors:
            return False

        len_vectors = len(vectors)
        for batch_index in range(0, len_vectors, batch_size):
            upsert_response = self._index.upsert(
                vectors=vectors[batch_index:batch_index + batch_size])
            print(f'[Pinecone.upsert] response: {upsert_response}')
            upserted = upsert_response.get('upserted_count', 0) if upsert_response else 0
            if hasattr(upsert_response, 'upserted_count') and upserted >= min(len_vectors - batch_index, batch_size):
                print(f'[Pinecone.upsert] upsert response count: {upserted}')
            else:
                return False
        return True

    def fetch(self, ids: List[str]):
        print(f'[Pinecone.fetch] ids: {ids}')
        if not ids:
            return None

        fetch_response = self._index.fetch(ids)
        return fetch_response.get('vectors', None) if fetch_response else None
