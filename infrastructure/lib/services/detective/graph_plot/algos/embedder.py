from typing import List

from dstruct.model import Block, Chunk
from external.openai_ import OpenAI


class Embedder:
    def __init__(self, llm: OpenAI) -> None:
        self._llm = llm

    def _embeddable(self, chunks: List[Chunk]) -> str:
        chunk_strings = [chunk.text for chunk in chunks]
        
        MAX_TREE_BLOCKS_CHILDREN = 10
        while len(chunk_strings) > 1:
            chunk_strings_len = len(chunk_strings)
            temp_chunk_strings = []
            for i in range(0, chunk_strings_len, MAX_TREE_BLOCKS_CHILDREN):
                chunk_strings_input = '\n\n'.join(chunk_strings[i : min(i + MAX_TREE_BLOCKS_CHILDREN, chunk_strings_len)])
                stringified_block = self._llm.summarize(chunk_strings_input)
                temp_chunk_strings.append(stringified_block)
            chunk_strings = temp_chunk_strings
        if len(chunk_strings) != 1:
            raise Exception("[Embedder._embeddable]: len(chunk_strings) != 1")
        return chunk_strings[0]

    def block_with_embeddings(self, block: Block) -> None:
        unstructured_properties = block.get_unstructured_properties()
        if not unstructured_properties:
            block.embedding = self._llm.embed(str(block.properties))
            return

        chunks = []
        for property in unstructured_properties:
            chunks.extend(property.chunks)
        condensed_chunk_string = self._embeddable(chunks)
        block.embedding = self._llm.embed(condensed_chunk_string)

        for property in unstructured_properties:
            if len(property.chunks) == 1:
                property.chunks[0].embedding = block.embedding
                continue
            for chunk in property.chunks:
                chunk.embedding = self._llm.embed(chunk.text)
