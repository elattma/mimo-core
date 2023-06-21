from typing import List

from dstruct.model import Block, Chunk, UnstructuredProperty
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
        chunks = []
        unstructured_properties = block.get_unstructured_properties()
        if unstructured_properties:
            for property in unstructured_properties:
                if not property.chunks:
                    continue
                chunks.extend(property.chunks)
                for chunk in property.chunks:
                    chunk.embedding = self._llm.embed(chunk.text)
            condensed_chunk_string = self._embeddable(chunks)
            block.embedding = self._llm.embed(condensed_chunk_string)
        else:
            block.embedding = self._llm.embed(str(block.properties))
