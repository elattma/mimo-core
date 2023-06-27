import logging
from math import sqrt
from typing import Dict, List, Literal

import tiktoken
from context_agent.model import Request
from dstruct.model import (Block, Chunk, StructuredProperty,
                           UnstructuredProperty)

_logger = logging.getLogger('Reranker')

MeasurementMethod = Literal['euclidean_distance', 'cosine_similarity', 'cohere_ai_ranker']

class Reranker:
    def __init__(self, log_level: int) -> None:
        _logger.setLevel(log_level)

    def _count_tokens(self, string: str, encoding_name: str) -> int:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(string)
        return len(tokens)

    def _count_tokens_chunk(self, chunk: Chunk, encoding_name: str) -> int:
        return self._count_tokens(chunk.text, encoding_name)

    def _count_tokens_block(self, block: Block, encoding_name: str) -> int:
        total_tokens = 0
        for property in block.properties:
            if isinstance(property, UnstructuredProperty):
                for chunk in property.chunks:
                    total_tokens += self._count_tokens_chunk(chunk, encoding_name)
            elif isinstance(property, StructuredProperty):
                total_tokens += self._count_tokens(f'{property.key}: {property.value}', encoding_name)
        return total_tokens

    def _euclidean_distance(self, x, y):
        # TODO: remove once we start embedding chunks
        if not x and not y:
            return 1

        return sqrt(sum([(x[i] - y[i]) ** 2 for i in range(len(x))]))

    def _sort(self, focal_embedding: List[float], blocks: List[Block]) -> None:
        for block in blocks:
            for property in block.properties:
                if not (isinstance(property, UnstructuredProperty) and len(property.chunks) > 1):
                    continue
                
                property.chunks.sort(key=lambda chunk: self._euclidean_distance(focal_embedding, chunk.embedding))
        
        blocks.sort(key=lambda block: self._euclidean_distance(block.embedding, focal_embedding))

    def _rank(self, request: Request, blocks: List[Block]) -> List[int]:
        pass

    def minify(self, request: Request, blocks: List[Block], measurement_method: MeasurementMethod, encoding_name: str) -> None:
        _logger.debug(f'[minify] {len(blocks)} blocks with token_limit {request.token_limit} and block_limit {request.end.limit}')
        if not (request and blocks and measurement_method and encoding_name):
            _logger.error(f'[minify] missing required arguments (request: {request}, blocks: {blocks}, measurement_method: {measurement_method}, encoding_name: {encoding_name})')
            return

        # sort blocks and chunks
        if measurement_method == 'cohere_ai_ranker':
            self._rank(request, blocks)
        else:
            self._sort(request.end.embedding, blocks)

        if request.end.limit:
            blocks = blocks[:request.end.limit]
            return
        if not request.token_limit:
            blocks = blocks[:10]
            return

        # count tokens
        block_to_tokens_map: Dict[str, int] = {}
        total_token_count = 0
        for block in blocks:
            token_count = self._count_tokens_block(block, encoding_name)
            block_to_tokens_map[block.id] = token_count
            total_token_count += token_count
        
        if total_token_count < request.token_limit:
            return
        
        # pop blocks until total token count is below limit besides the last block
        while len(blocks) > 1:
            last_block = blocks[-1]
            last_block_token_count = block_to_tokens_map[last_block.id]

            if total_token_count - last_block_token_count < request.token_limit:
                break

            total_token_count -= last_block_token_count
            blocks.pop()

        # pop chunks and even properties from last block until total token count is below limit
        if total_token_count > request.token_limit:
            last_block = blocks[-1]

            # first pop least relevant chunks from properties with #chunks > 1
            all_chunks: List[Chunk] = []
            chunk_to_property: Dict[str, UnstructuredProperty] = {}
            chunk_to_tokens: Dict[str, int] = {}
            property_to_chunks_count: Dict[UnstructuredProperty, int] = {}
            for property in last_block.properties:
                if not (isinstance(property, UnstructuredProperty) and len(property.chunks) > 1):
                    continue
                all_chunks.extend(property.chunks)
                for chunk in property.chunks:
                    chunk_to_property[chunk.text] = property
                property_to_chunks_count[property] = len(property.chunks)
                chunk_to_tokens[chunk.text] = self._count_tokens_chunk(chunk, encoding_name)

            all_chunks.sort(key=lambda chunk: self._euclidean_distance(chunk.embedding, last_block.embedding))
            while all_chunks:
                chunk = all_chunks.pop()
                property = chunk_to_property[chunk.text]
                if not property_to_chunks_count[property]:
                    continue
                property_to_chunks_count[property] -= 1
                total_token_count -= chunk_to_tokens[chunk.text]
                chunk_to_property[chunk.text].chunks.remove(chunk)
                if total_token_count < request.token_limit:
                    break
        _logger.debug(f'[minify] minified to {len(blocks)} blocks with {total_token_count} tokens')