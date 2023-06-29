import logging
from typing import List

from cohere import Client

_logger = logging.getLogger('Cohere')

class Cohere:
    def __init__(self, api_key: str, log_level: int) -> None:
        self._client = Client(api_key)

        _logger.setLevel(log_level)

    def rank(self, query: str, documents: List[str], top_n: int = None, model: str = 'rerank-english-v2.0') -> List[float]:
        response = self._client.rerank(
            model=model,
            query=query,
            documents=documents,
            top_n=top_n
        )
        _logger.debug(f'[rank] response: {response}')
        results = response.results if response else None
        if results:
            results.sort(key=lambda result: result.index)
        return [result.relevance_score for result in results] if results else []
