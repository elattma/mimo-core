from typing import List

from graph.blocks import (BlockStream, BodyBlock, CommentBlock, ContactBlock,
                          DealBlock, MemberBlock, SummaryBlock, TitleBlock)
from graph.neo4j_ import Name
from external.openai_ import OpenAI

MAX_OPENAI_LEN = 2000

class Namer:
    def __init__(self, openai: OpenAI):
        self._openai = openai

    def get_block_names(self, block_stream: BlockStream) -> set[Name]:
        if not block_stream:
            return []
        
        names: List[Name] = []
        if block_stream.label == SummaryBlock._LABEL:
            names.extend(self._get_unstructured_names([block.text for block in block_stream.blocks]))
        elif block_stream.label == BodyBlock._LABEL:
            names.extend(self._get_unstructured_names([block.text for block in block_stream.blocks]))
        elif block_stream.label == TitleBlock._LABEL:
            names.extend(self._get_unstructured_names([block.text for block in block_stream.blocks]))
        elif block_stream.label == CommentBlock._LABEL:
            for block in block_stream.blocks:
                author_name = Name(id=block.author.id, value=block.author.value)
                names.append(author_name)
            names.extend(self._get_unstructured_names([block.text for block in block_stream.blocks]))
        elif block_stream.label == DealBlock._LABEL:
            for block in block_stream.blocks:
                names.append(Name(id=block.name.id, value=block.name.value))
                names.append(Name(id=block.owner.id, value=block.owner.value))
                names.append(Name(id=block.contact.id, value=block.contact.value))
        elif block_stream.label == ContactBlock._LABEL:
            for block in block_stream.blocks:
                names.append(Name(id=block.name.id, value=block.name.value))
                names.append(Name(id=block.created_by.id, value=block.created_by.value))
        elif block_stream.label == MemberBlock._LABEL:
            for block in block_stream.blocks:
                names.append(Name(id=block.name.id, value=block.name.value))
        return set(names)
    
    def _get_unstructured_names(self, unstructured_texts: List[str]) -> set[Name]:
        return []
        # collector = []
        # collector_len = 0
        # names = set()
        # for unstructured_text in unstructured_texts:
        #     if not unstructured_text:
        #         continue
        #     if collector_len + len(unstructured_text) > MAX_OPENAI_LEN:
        #         unstructured_names = self._openai.names('\n\n'.join(collector))
        #         names.update(unstructured_names)
        #         collector = []
        #         collector_len = 0
        #     collector.append(unstructured_text)
        #     collector_len += len(unstructured_text)
        # if len(collector) > 0:
        #     unstructured_names = self._openai.names('\n\n'.join(collector))
        #     names.update(unstructured_names)
        # return names