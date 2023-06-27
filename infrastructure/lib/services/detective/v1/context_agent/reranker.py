import logging
from math import sqrt
from typing import Dict, List

import tiktoken
from context_agent.model import Request
from dstruct.model import (Block, Chunk, StructuredProperty,
                           UnstructuredProperty)
from external.cohere_ import Cohere

_logger = logging.getLogger('Reranker')


class Reranker:
    def __init__(self, cohere: Cohere, log_level: int) -> None:
        self._cohere = cohere
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
            return 1.

        return sqrt(sum([(x[i] - y[i]) ** 2 for i in range(len(x))]))

    def _rank_blocks(self, focal_embedding: List[float], blocks: List[Block]) -> Dict[str, float]:
        block_to_rank_map: Dict[str, float] = {}
        for block in blocks:
            block_to_rank_map[block.id] = self._euclidean_distance(block.embedding, focal_embedding)
        return block_to_rank_map

    def _rank_chunks(self, raw_request: str, blocks: List[Block]) -> Dict[str, float]:
        _logger.debug(f'[rank] ranking {len(blocks)} blocks')
        chunks: List[Chunk] = []
        for block in blocks:
            unstructured_properties = block.get_unstructured_properties()
            if unstructured_properties:
                for unstructured_property in unstructured_properties:
                    for chunk in unstructured_property.chunks:
                        chunks.append(chunk)
        if not chunks:
            _logger.error(f'[rank] no chunks found')
            return {}
        
        _logger.debug(f'[rank] ranking {len(chunks)} chunks')
        ranks = self._cohere.rank(raw_request, [chunk.text for chunk in chunks])
        if not ranks:
            _logger.error(f'[rank] no ranks returned from cohere')
            return {}

        chunk_to_rank_map: Dict[str, float] = {}
        for chunk, rank in zip(chunks, ranks):
            chunk_to_rank_map[chunk.text] = rank
        
        return chunk_to_rank_map

    def minify(self, request: Request, blocks: List[Block], encoding_name: str) -> None:
        _logger.debug(f'[minify] {len(blocks)} blocks with token_limit {request.token_limit} and block_limit {request.end.limit}')
        if not (request and blocks and encoding_name):
            _logger.error(f'[minify] missing required arguments (request: {request}, blocks: {blocks}, encoding_name: {encoding_name})')
            return

        blocks_to_rank_map: Dict[str, float] = self._rank_blocks(request.end.embedding, blocks)
        blocks = sorted(blocks, key=lambda block: blocks_to_rank_map[block.id])

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
            chunks_to_rank_map: Dict[str, float] = self._rank_chunks(request.raw, blocks[-1:])

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

            all_chunks.sort(key=lambda chunk: chunks_to_rank_map[chunk.text])
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