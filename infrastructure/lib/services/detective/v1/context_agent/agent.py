from typing import List

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
        text = raw_query
        if block_query.concepts:
            text = ' '.join(block_query.concepts)
        block_query.embedding = self._llm.embed(text)
    
    def fetch(self, request: Request) -> List[Block]:
        print('[ContextAgent.fetch] Generating context...')

        # TODO: overrides and only if they're not enough do we formulate a query
        # TODO: make sure overrides are respected and only prompt for what more we need to know
        self._with_llm_reasoning(request)

        # if request:
        #     self._with_embedding(request.start_node, request.raw)
        # self._with_embedding(request.end_node, request.raw)

        # # first we try the raw query and see if that yields any results
        # blocks: List[Block] = self._dstruct.query(request.end_node, request.start_node, with_embeddings=True, with_data=True)

        # if not blocks:
        #     print(f'[ContextAgent.fetch] No results for raw query {request.end_node} -> {request.start_node}')
        #     print(f'[ContextAgent.fetch] Trying to formulate a broader query... FIXME: not implemented yet')
        #     # TODO: if that doesn't work, we try to formulate a broader query based on our own reasoning of the request and knowledge of our data structure
        #     return None
        
        # return self._weaver.minify(request.end_node.embedding, blocks, request.token_limit, num_blocks=request.end_node.limit if request.end_node.limit else None)
    
    def _with_llm_reasoning(self, request: Request) -> None:
        print(f'[ContextAgent._with_llm_reasoning] Decorating with language reasoning for request: {request}')
        block_descriptions = str(SUPPORTED_BLOCK_LABELS) # TODO: fill this in somehow, dynamically or statically from config

        block_query_schema = BlockQuery.schema()
        block_query_schema.get('properties', {}).pop('ids')
        block_query_schema.get('properties', {}).pop('integrations')
        block_query_schema.get('properties', {}).pop('embedding')
        block_query_schema['properties']['labels']['description'] += block_descriptions
        print(block_query_schema)

        response = self._llm.function_call(
            messages=[{
                'role': 'system',
                'content': (
                    'Pretend you are a context agent for a large company. '
                    'Your job is to take a query and break it down using '
                    'language reasoning so that you can find the right data '
                    'in the company\'s database. ' #TODO: do all prompting here and just give simple descriptions under each field. Few-shot examples.
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
                        'end_block': block_query_schema,
                        'start_block': block_query_schema
                    },
                    'required': ['end_block']
                }
            }],
            function_call={'name': 'interpret_and_formulate_request'}
        )
        print(response)
        for key, value in response.items():
            if hasattr(Request, key):
                setattr(request, key, BlockQuery(**value))
            else:
                print(f'[ContextAgent._with_llm_reasoning] Warning: unknown key: {key}, value: {value}')
        print(f'[ContextAgent._with_llm_reasoning] Decorated with language reasoning for request: {request}')
    
