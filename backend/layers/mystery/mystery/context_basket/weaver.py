import json
from math import sqrt
from typing import Any, List

from graph.blocks import BlockStream
from graph.neo4j_ import Document
from graph.translator import Translator
from mystery.util import count_tokens

from .model import Context, ContextBasket, Request, Source


class BasketWeaver:
    @staticmethod
    def weave_context_basket(request: Request, documents: List[Document]) -> ContextBasket:
        if not (request and documents):
            return None

        contexts: List[Context] = []
        for document in documents:
            source = Source(
                page_id=document.id,
                integration=document.integration
            )

            blocks = [edge.target for edge in document.consists]
            block_streams: List[BlockStream] = []
            for block in blocks:
                try:
                    block_stream_dict: List[dict] = json.loads(block.content)
                    block_stream = BlockStream.from_dict(
                        block.label, block_stream_dict)
                    block_streams.append(block_stream)
                except Exception as e:
                    print('failed to cast to a block stream!')
                    print(block)
                    print(e)
            translated = Translator.translate_document(
                document.integration, block_streams)
            tokens = count_tokens(translated, request.encoding_name)
            contexts.append(Context(
                source=source,
                blocks=blocks,
                translated=translated,
                tokens=tokens
            ))
        return ContextBasket(
            request=request,
            contexts=contexts
        )

    @staticmethod
    def minify_context_basket(context_basket: ContextBasket, limit_tokens: int) -> None:
        if context_basket.tokens <= limit_tokens:
            return

        request = context_basket.request
        encoding_name = request.encoding_name
        sort_contexts(request.embedding, context_basket.contexts)
        remaining_tokens = limit_tokens
        context_counter = 0
        contexts_len = len(context_basket.contexts)
        while remaining_tokens > 0 and context_counter < contexts_len - 1:
            context = context_basket.contexts[0]
            context_tokens = count_tokens(context, encoding_name)
            remaining_tokens -= context_tokens
            if remaining_tokens < 0:
                break
            context_basket.contexts.pop(0)
            context_counter += 1


def euclidean_distance(row1, row2) -> float:
    distance = 0.0
    for i in range(len(row1)-1):
        distance += (row1[i] - row2[i])**2
    return sqrt(distance)


def sort_list_embeddings(focal_embedding: List[float], _list: List[Any], embeddings: List[List[float]]) -> None:
    if not (focal_embedding and _list and embeddings and len(_list) == len(embeddings)):
        print('sort_list_embeddings: invalid input!')
        return

    element_distance_tuples = List[tuple[Any, float]] = []
    for element, embedding in zip(_list, embeddings):
        distance: float = euclidean_distance(focal_embedding, embedding)
        element_distance_tuples.append((element, distance))

    element_distance_tuples.sort(key=lambda x: x[1], reverse=True)


def sort_contexts(focal_embedding: List[float], contexts: List[Context]) -> None:
    context_embeddings = []
    for context in contexts:
        sort_list_embeddings(focal_embedding, context.blocks, [
                             block.embedding for block in context.blocks])
        context_embeddings.append(context.blocks[-1].embedding)
    sort_list_embeddings(focal_embedding, contexts, context_embeddings)
