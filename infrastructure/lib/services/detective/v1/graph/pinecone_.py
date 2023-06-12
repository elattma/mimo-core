from typing import Dict, List

import pinecone
from graph.model import SemanticFilter


class Pinecone:
    def __init__(self, api_key: str, environment: str, index_name: str = 'beta'):
        pinecone.init(api_key=api_key, environment=environment)
        indexes = pinecone.list_indexes()
        if indexes and index_name in indexes:
            self._index = pinecone.Index(index_name=index_name)
        if not self._index:
            raise Exception('Pinecone index or library not found')
        
    def _with_library(self, library: str, id: str):
        return f'{library}#{id}'
    
    def _without_library(self, row_id: str):
        return row_id.split('#')[-1]

    def fetch(self, library: str, ids: List[str]) -> Dict[str, List[float]]:
        if not (self._index and library and ids and len(ids) > 0):
            return None

        fetch_response = self._index.fetch(ids=[self._with_library(library, id) for id in ids])
        id_to_embedding: Dict[str, List[float]] = {}
        for id, vector in fetch_response.items():
            id_to_embedding[self._without_library(id)] = vector.values
        return id_to_embedding

    def query(self, embedding: List[float], filter: SemanticFilter, k: int = 5):
        if not (self._index and embedding and len(embedding) > 0):
            return None

        query_response = self._index.query(
            vector=embedding,
            top_k=k,
            filter=filter.to_dict(),
            include_metadata=True,
            include_values=True
        )

        return query_response.get('matches', None) if query_response else None
