import json
from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from typing import Any, Dict, List

from mystery.query import Query, Request
from mystery.util import count_tokens


@dataclass
class Block:
    id: str
    label: str
    last_updated_timestamp: int
    blocks: List[Dict]
    embedding: List[float] = None

@dataclass
class Context:
    connection: str
    source: str
    blocks: List[Block]
    tokens: int = None

@dataclass
class ContextBasket:
    request: Request
    contexts: List[Context] = field(default_factory=list)
    tokens: int = 0

    def append(self, context: Context) -> None:
        self.tokens += context.tokens
        self.contexts.append(context)

    def extend(self, contexts: List[Context]) -> None:
        for context in contexts:
            self.tokens += context.tokens
        self.contexts.extend(contexts)

    def pop(self, pos: int = -1) -> Context:
        if self.contexts:
            context = self.contexts.pop(pos)
            self.tokens -= context.tokens
            return context

    def __iter__(self):
        return iter(self.contexts)

    def __str__(self):
        stringified = self.request.text
        stringified += '\n--------\n'
        stringified += '\n'.join([str(context.blocks) for context in self.contexts])
        return stringified

@dataclass
class DataError(Enum):
    QUERY_FORMATION_FAILURE = 'Failed to dynamically formulate query!'
    FETCH_PAGES_FAILURE = 'Failed to fetch pages!'
    FILTERED_PAGES_FAILURE = 'Failed to fetched filtered pages!'
    DECORATE_EMBEDDINGS_FAILURE = 'Failed to decorate pages with embeddings!'
    WEAVE_CONTEXT_FAILURE = 'Failed to weave context!'
    MINIFY_CONTEXT_FAILURE = 'Failed to minify context!'

@dataclass
class DataRequest:
    library: str
    request: str
    query: Query
    max_tokens: int

@dataclass
class DataResponse:
    successful: bool
    context_basket: ContextBasket
    error: DataError = None


class BasketWeaver:
    def __init__(self):
        pass

    def translate_graph_blocks(self, blocks: List[Block], integration: str = None) -> str:
        if not blocks:
            return None

        block_streams: List[BlockStream] = []
        for block in blocks:
            try:
                block_stream_dict: List[dict] = json.loads(block.content)
                block_stream = BlockStream.from_dict(block.label, block_stream_dict)
                block_streams.append(block_stream)
            except Exception as e:
                print(f'[Weaver] Failed to cast to a block stream! {block}. Exception: {e}'.replace('\n', '||'))
                return None
        
        if integration: 
            translated = Translator.translate_document(integration, block_streams)
        else:
            translated = Translator.translate_block_streams(block_streams)
        return translated

    def weave_context_basket(self, request: Request, blocks: List[Dict]) -> ContextBasket:
        if not (request and documents):
            return None

        context_basket = ContextBasket(request=request)
        for document in documents:
            source = Source(
                page_id=document.id,
                integration=document.integration
            )

            blocks = [edge.target for edge in document.consists]
            translated = self.translate_graph_blocks(blocks, source.integration)
            tokens = count_tokens(translated, request.encoding_name)
            context_basket.append(Context(
                source=source,
                blocks=blocks,
                translated=translated,
                tokens=tokens
            ))
        print('[DataAgent] Context generated! Raw:')
        print(str(context_basket).replace('\n', '||'))
        return context_basket

    def minify_context_basket(self, context_basket: ContextBasket, limit_tokens: int) -> None:
        print(f'[Weaver] Minifying context basket with {len(context_basket.contexts)} contexts and {context_basket.tokens} tokens. Limit: {limit_tokens} tokens.')
        if context_basket.tokens <= limit_tokens:
            return

        request = context_basket.request
        encoding_name = request.encoding_name
        context_basket.contexts = sort_contexts(request.embedding, context_basket.contexts)
        remaining_tokens = context_basket.tokens - limit_tokens
        context_counter = 0
        contexts_len = len(context_basket.contexts)
        while remaining_tokens > 0 and context_counter < contexts_len - 1:
            context = context_basket.contexts[0]
            context_tokens = count_tokens(context.translated, encoding_name)
            remaining_tokens -= context_tokens
            if remaining_tokens < 0:
                break
            context = context_basket.pop(0)
            context_counter += 1
        
        print(f'[Weaver] Minified context basket contexts with {len(context_basket.contexts)} contexts and {context_basket.tokens} tokens. Limit: {limit_tokens} tokens.')
        if context_basket.tokens <= limit_tokens:
            return
        
        blocks_to_remove = set()
        blocks: List[Block] = []
        for context in context_basket.contexts:
            blocks.extend(context.blocks)
        blocks = sort_list_embeddings(request.embedding, blocks, [block.embedding for block in blocks])
        remaining_tokens = context_basket.tokens - limit_tokens
        remaining_tokens += sum([Translator.get_extra_document_tokens(context.source.integration, len(context.blocks)) for context in context_basket.contexts])
        blocks_len = len(blocks)
        block_counter = 0
        while remaining_tokens > 0 and block_counter < blocks_len - 1:
            block = blocks[block_counter]
            translated = self.translate_graph_blocks([block])
            block_tokens = count_tokens(translated, encoding_name)
            remaining_tokens -= block_tokens
            blocks_to_remove.add(block)
            block_counter += 1
        
        for context in context_basket.contexts:
            context.blocks = [block for block in context.blocks if block not in blocks_to_remove]
            if context.blocks:
                context.translated = self.translate_graph_blocks(context.blocks, context.source.integration)
                context.tokens = count_tokens(context.translated, encoding_name)
        context_basket.contexts = [context for context in context_basket.contexts if len(context.blocks) > 0]
        context_basket.tokens = sum([context.tokens for context in context_basket.contexts])
        print(f'[Weaver] Minified context basket blocks with {len(context_basket.contexts)} contexts and {context_basket.tokens} tokens. Limit: {limit_tokens} tokens.')
        print(f'[DataAgent] Context generated! Minified: ')
        print(str(context_basket).replace('\n', '||'))

def euclidean_distance(row1, row2) -> float:
    distance = 0.0
    for i in range(len(row1)-1):
        distance += (row1[i] - row2[i])**2
    return sqrt(distance)


def sort_list_embeddings(focal_embedding: List[float], _list: List[Any], embeddings: List[List[float]]) -> List[Any]:
    if not (focal_embedding and _list and embeddings and len(_list) == len(embeddings)):
        print('[Weaver] Invalid input in sort list embeddings!')
        return

    element_distance_tuples: List[tuple[Any, float]] = []
    for element, embedding in zip(_list, embeddings):
        distance: float = euclidean_distance(focal_embedding, embedding)
        element_distance_tuples.append((element, distance))

    element_distance_tuples.sort(key=lambda x: x[1], reverse=True)
    return [tuple[0] for tuple in element_distance_tuples]


def sort_contexts(focal_embedding: List[float], contexts: List[Context]) -> List[Context]:
    context_embeddings = []
    for context in contexts:
        context.blocks = sort_list_embeddings(focal_embedding, context.blocks, [block.embedding for block in context.blocks])
        context_embeddings.append(context.blocks[-1].embedding)
    return sort_list_embeddings(focal_embedding, contexts, context_embeddings)
