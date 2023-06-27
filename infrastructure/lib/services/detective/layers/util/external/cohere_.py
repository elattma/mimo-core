import logging
from typing import List

from cohere import Client

_logger = logging.getLogger('Cohere')

class Cohere:
    def __init__(self, api_key: str, log_level: int) -> None:
        self._client = Client(api_key)

        _logger.setLevel(log_level)

    def rank(self, query: str, documents: List[str], top_n: int = None, return_documents: bool = False, model: str = 'rerank-english-v2.0') -> List[float]:
        response = self._client.rerank(
            model=model,
            query=query,
            documents=documents,
            return_documents=return_documents,
            top_n=top_n
        )
        _logger.debug(f'[rank] response: {response}')
        results = response.get('results', []) if response else []
        in_order_results = sorted(results, key=lambda result: result.get('index'))
        return [result.get('relevance_score') for result in in_order_results]
