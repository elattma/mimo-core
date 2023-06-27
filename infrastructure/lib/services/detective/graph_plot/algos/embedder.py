from logging import getLogger
from typing import List

from dstruct.model import Block, Chunk
from external.openai_ import OpenAI


class Embedder:
    def __init__(self, llm: OpenAI, log_level: int) -> None:
        self._llm = llm

        self._logger = getLogger('Embedder')
        self._logger.setLevel(log_level)

    def _summarize(self, text: str) -> str:
        return self._llm.chat_completion(
            messages=[{
                'role': 'system',
                'content': (
                    'Imagine you are a Data Genius who is able '
                    'to classify and understand any JSON data. '
                    'Summarize the provided JSON using simple sentences. '
                    'Preserve all important keywords, nouns, proper nouns, dates, concepts. '
                    'Do not use pronouns. Write as much as you need to preserve all important information!'
                )
            }, {
                'role': 'user',
                'content': text
            }]
        )

    def _embeddable(self, chunks: List[Chunk]) -> str:
        chunk_strings: List[str] = ['']
        for chunk in chunks:
            if len(chunk_strings[-1]) + len(chunk.text) > 2000:
                chunk_strings.append('')
            chunk_strings[-1] += chunk.text

        MAX_TREE_BLOCKS_CHILDREN = 10
        while len(chunk_strings) > 1:
            chunk_strings_len = len(chunk_strings)
            temp_chunk_strings = []
            for i in range(0, chunk_strings_len, MAX_TREE_BLOCKS_CHILDREN):
                chunk_strings_input = '\n\n'.join(chunk_strings[i : min(i + MAX_TREE_BLOCKS_CHILDREN, chunk_strings_len)])
                stringified_block = self._summarize(chunk_strings_input)
                temp_chunk_strings.append(stringified_block)
            chunk_strings = temp_chunk_strings
        if len(chunk_strings) != 1:
            raise Exception("[_embeddable]: len(chunk_strings) != 1")
        return chunk_strings[0]

    def block_with_embeddings(self, block: Block) -> None:
        unstructured_properties = block.get_unstructured_properties()
        if not unstructured_properties:
            block.embedding = self._llm.embed(str(block.properties))
            self._logger.debug(f'[block_with_embeddings] embedded structured block for {block.id}')
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
        self._logger.debug(f'[block_with_embeddings] embedded unstructured block for {block.id}')
