from typing import Dict, List

from context_agent.model import Request
from context_agent.weaver import Weaver
from dstruct.base import DStruct
from dstruct.model import Block, BlockQuery
from external.openai_ import OpenAI
from store.block_state import SUPPORTED_BLOCK_LABELS


class ContextAgent:
    def __init__(
        self,
        dstruct: DStruct,
        openai: OpenAI
    ) -> None:
        print('[ContextAgent.__init__] starting')
        self._dstruct = dstruct
        self._llm = openai
        self._weaver = Weaver()
        print('[ContextAgent.__init__] completed')

    def _with_embedding(self, block_query: BlockQuery, raw_query: str) -> None:
        if block_query.search_method != 'relevant':
            return
        block_query.embedding = self._llm.embed(block_query.concepts if block_query.concepts else raw_query)
    
    def fetch(self, request: Request) -> List[Block]:
        print('[ContextAgent.fetch] Generating context...')

        if request.end and request.end.search_method:
            print(f'[ContextAgent.fetch] search method specified {request.end.search_method}. skipping llm reasoning...')
        else:
            self._with_llm_reasoning(request)


        if request.start:
            self._with_embedding(request.start, request.raw)
        self._with_embedding(request.end, request.raw)

        # # first we try the raw query and see if that yields any results
        blocks: List[Block] = self._dstruct.query(request.end, request.start, with_embeddings=True, with_data=True)

        # if not blocks:
        #     print(f'[ContextAgent.fetch] No results for raw query {request.end} -> {request.start}')
        #     print(f'[ContextAgent.fetch] Trying to formulate a broader query... FIXME: not implemented yet')
        #     # TODO: if that doesn't work, we try to formulate a broader query based on our own reasoning of the request and knowledge of our data structure
        #     return None
        
        # return self._weaver.minify(request.end.embedding, blocks, request.token_limit, num_blocks=request.end.limit if request.end.limit else None)

    def _with_llm_reasoning(self, request: Request) -> None:
        print(f'[ContextAgent._with_llm_reasoning] decorating with language reasoning for request: {request}')

        block_query_properties: Dict[str, Dict] = BlockQuery.schema().get('properties')
        block_query_properties.pop('ids')
        block_query_properties.pop('integrations')
        block_query_properties.pop('embedding')
        block_query_properties['labels']['items']['enum'] = list(SUPPORTED_BLOCK_LABELS) # TODO: fill this in somehow, dynamically or statically from config
        print(f'[ContextAgent._with_llm_reasoning] block_query_properties = {block_query_properties}')

        specified_end_properties: Dict[str, Dict] = {}
        if request.end:
            for key, value in request.end.dict().items():
                if value:
                    specified_end_properties[key] = block_query_properties[key]
        print(f'[ContextAgent._with_llm_reasoning] specified_end_properties = {specified_end_properties}')
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
                    print(f'[ContextAgent._with_llm_reasoning] skipping {key} because it is already specified')
                    continue
                setattr(request.end, key, value)
        print(f'[ContextAgent._with_llm_reasoning] decorated with language reasoning for request: {request}')
    
