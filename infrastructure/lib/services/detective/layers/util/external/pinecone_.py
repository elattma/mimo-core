from logging import getLogger
from typing import Any, Dict, List

import pinecone

_logger = getLogger('Pinecone')

class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str, log_level: int):
        _logger.setLevel(log_level)

        _logger.debug('[__init__] starting')
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        if not self._index:
            raise Exception('pinecone index not found')
        _logger.debug('[__init__] completed')
        
    def delete(self, ids: List[str]) -> bool:
        _logger.debug(f'[Pinecone.delete] ids: {ids}')
        if not ids:
            return False

        delete_response = self._index.delete(ids)
        _logger.debug(f'[Pinecone.delete] response: {delete_response}')
        return True

    def upsert(self, vectors: List[dict], batch_size: int = 100) -> bool:
        _logger.debug(f'[Pinecone.upsert] vectors: {str(len(vectors) if vectors else 0)} batch_size: {str(batch_size)}')
        if not vectors:
            return False

        len_vectors = len(vectors)
        for batch_index in range(0, len_vectors, batch_size):
            upsert_response = self._index.upsert(
                vectors=vectors[batch_index:batch_index + batch_size])
            _logger.debug(f'[Pinecone.upsert] response: {upsert_response}')
            upserted = upsert_response.get('upserted_count', 0) if upsert_response else 0
            if hasattr(upsert_response, 'upserted_count') and upserted >= min(len_vectors - batch_index, batch_size):
                _logger.debug(f'[Pinecone.upsert] upsert response count: {upserted}')
            else:
                return False
        return True

    def fetch(self, ids: List[str]):
        _logger.debug(f'[Pinecone.fetch] ids: {ids}')
        if not ids:
            return None

        fetch_response = self._index.fetch(ids)
        return fetch_response.get('vectors', None) if fetch_response else None
    
    def query(self, embedding: List[float], filter: Dict[str, Any], top_k: int, include_metadata: bool = True, include_values: bool = True):
        _logger.debug(f'[Pinecone.query] filter {filter}, top_k {top_k}, include_metadata {include_metadata}, include_values {include_values}')
        query_response = self._index.query(
            vector=embedding,
            top_k=top_k,
            filter=filter,
            include_metadata=include_metadata,
            include_values=include_values
        )

        return query_response.get('matches', None) if query_response else None
