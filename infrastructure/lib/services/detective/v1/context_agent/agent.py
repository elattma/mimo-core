import logging
from typing import Dict, List

from context_agent.model import Request
from context_agent.reranker import Reranker
from dstruct.base import DStruct
from dstruct.model import Block, BlockQuery
from external.openai_ import OpenAI
from store.block_state import SUPPORTED_BLOCK_LABELS

_logger = logging.getLogger('ContextAgent')

class ContextAgent:
    def __init__(
        self,
        dstruct: DStruct,
        openai: OpenAI,
        reranker: Reranker,
        log_level: int
    ) -> None:
        _logger.setLevel(log_level)
        self._dstruct = dstruct
        self._llm = openai
        self._reranker = reranker

    def _with_embedding(self, block_query: BlockQuery, raw_query: str) -> None:
        if block_query.search_method != 'relevant':
            return
        block_query.embedding = self._llm.embed(block_query.concepts if block_query.concepts else raw_query)
    
    def fetch(self, request: Request) -> List[Block]:
        _logger.debug('[fetch] Generating context...')

        if request.end and request.end.search_method:
            _logger.debug(f'[fetch] search method specified {request.end.search_method}. skipping llm reasoning...')
        else:
            self._with_llm_reasoning(request)
        if request.start:
            self._with_embedding(request.start, request.raw)
        self._with_embedding(request.end, request.raw)

        # first we try the raw query and see if that yields any results
        blocks: List[Block] = self._dstruct.query(request.end, request.start, with_embeddings=True, with_data=True)

        if not blocks:
            _logger.debug(f'[fetch] No results for raw query {request.end} -> {request.start}')
            _logger.debug(f'[fetch] Trying to formulate a broader query... naive fallback')

            fallback_query = BlockQuery(
                search_method='relevant',
                concepts=request.end.concepts if request.end.concepts else request.raw,
                entities=None,
                absolute_time_start=None,
                absolute_time_end=None,
                relative_time=None,
                limit=request.end.limit if request.end.limit else 5,
                offset=request.end.offset if request.end.offset else 0,
                labels=request.end.labels if request.end.labels else None,
                ids=request.end.ids if request.end.ids else None,
                integrations=request.end.integrations,
                embedding=request.end.embedding,
            )

            blocks = self._dstruct.query(fallback_query)
            _logger.debug(f'[fetch] Fallback query {fallback_query} yielded {len(blocks)} results')
            return None
        
        self._reranker.minify(request, blocks, 'euclidean_distance', 'cl100k_base')
        return blocks

    def _with_llm_reasoning(self, request: Request) -> None:
        _logger.debug(f'[_with_llm_reasoning] decorating with language reasoning for request: {request}')

        block_query_properties: Dict[str, Dict] = BlockQuery.schema().get('properties')
        block_query_properties.pop('ids')
        block_query_properties.pop('integrations')
        block_query_properties.pop('embedding')
        block_query_properties['labels']['items']['enum'] = list(SUPPORTED_BLOCK_LABELS) # TODO: fill this in somehow, dynamically or statically from config
        _logger.debug(f'[_with_llm_reasoning] block_query_properties = {block_query_properties}')

        specified_end_properties: Dict[str, Dict] = {}
        if request.end:
            for key, value in request.end.dict().items():
                if value:
                    specified_end_properties[key] = block_query_properties[key]
        _logger.debug(f'[_with_llm_reasoning] specified_end_properties = {specified_end_properties}')
        specified_end_properties_description = (
            'Properties that you already know about the end block that the user is searching for: '
            f'{str(specified_end_properties)}'
        ) if specified_end_properties else ""

        response = self._llm.function_call(
            messages=[{
                'role': 'system',
                'content': (
                    'Pretend you are a context agent for a large company. '
                    'Your job is to take a query and break it down using '
                    'language reasoning so that you can find the right data '
                    'in the company\'s database. '
                    # TODO: add few shots and perhaps more context here
                )
            }, {
                'role': 'user',
                'content': request.raw
            }],
            functions=[{
                'name': 'interpret_and_formulate_request',
                'description': 'Use your language reasoning to interpret the user\'s request and formulate a query for the database.',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'end': {
                            'title': 'End Block',
                            'type': 'object',
                            'description': (
                                'The block that the user is searching for. This is the block that you need to find in the database. '
                                f'{specified_end_properties_description}'
                            ),
                            'properties': block_query_properties,
                        },
                        'start': {
                            'title': 'Start Block',
                            'type': 'object',
                            'description': 'The block that the user is starting from which is connected to the end block that the user is searching for.',
                            'properties': block_query_properties,
                        }
                    },
                    'required': ['end']
                }
            }],
            function_call={'name': 'interpret_and_formulate_request'}
        )
        start_json = response.get('start', None)
        if start_json:
            request.start = BlockQuery(**start_json)
        if not request.end:
            request.end = BlockQuery(**response.get('end', {}))
        else: 
            for key, value in response.get('end', {}).items():
                is_specified = specified_end_properties.get(key, None)
                if is_specified:
                    _logger.debug(f'[_with_llm_reasoning] skipping {key} because it is already specified')
                    continue
                setattr(request.end, key, value)
        _logger.debug(f'[_with_llm_reasoning] decorated with language reasoning for request: {request}')
    
