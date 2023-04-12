from typing import List, Set

from external.openai_ import OpenAI
from graph.blocks import (BlockStream, BodyBlock, CommentBlock, ContactBlock,
                          DealBlock, MemberBlock, SummaryBlock, TitleBlock)
from graph.neo4j_ import Name

MAX_OPENAI_LEN = 2000

# TODO: make this dynamic
names = ["Henry Pereira", "Morlong Associates", "Carissa", "Support", "Mitsue Tollner", "Printing Dimensions", "Donette Foller", "Truhlar And Truhlar Attys", "Sage Wieser", "Google", "The Fivetran Team", "Mimo Admin", "OpenAI", "Alex Laubscher", "Zendesk", "\" Amazon Web Services (AWS)\"" , "Chanay", "Josephine Darakjy", "Chapman", "Simon Morasca", "James Venere", "Chemel", "Commercial Press", "Leota Dilliard", "Snowflake", "Kris Marrier", "Leota Dilliard", "Mitsue Tollner", "Simon Morasca", "Donette Foller", "James Venere", "Josephine Darakjy", "John Butt", "Capla Paprocki", "Feltz Printing Service", "Kris Marrier", "King", "Zendesk", "Zendesk", "Mimo", "The Neo4j Team", "Alan at Retool", "Fivetran Notifications", "\" Alex Laubscher (Mimo)\"" , "Hailee Draughon", "Isaia Taotua", "Zoho CRM", "Atlassian", "Webflow University", "Ivan at Notion", "Sage Wieser"]

class Namer:
    def __init__(self, openai: OpenAI):
        self._openai = openai

    def get_block_names(self, block_stream: BlockStream) -> set[Name]:
        if not block_stream:
            return []
        
        names: set[Name] = set()
        if block_stream.label == CommentBlock._LABEL:
            for block in block_stream.blocks:
                names.add(Name(id=block.author.id, value=block.author.value))
        elif block_stream.label == DealBlock._LABEL:
            for block in block_stream.blocks:
                names.add(Name(id=block.name.id, value=block.name.value))
                names.add(Name(id=block.owner.id, value=block.owner.value))
                names.add(Name(id=block.contact.id, value=block.contact.value))
        elif block_stream.label == ContactBlock._LABEL:
            for block in block_stream.blocks:
                names.add(Name(id=block.name.id, value=block.name.value))
                names.add(Name(id=block.created_by.id, value=block.created_by.value))
        elif block_stream.label == MemberBlock._LABEL:
            for block in block_stream.blocks:
                names.add(Name(id=block.name.id, value=block.name.value))
        return names
    
    def infer_names(self, block_stream: BlockStream) -> set[Name]:
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
                names.append(Name(id=block.author.id, value=block.author.value))
            names.extend(self._get_unstructured_names([block.text for block in block_stream.blocks]))
        return set(names)
    
    def _get_unstructured_names(self, texts: List[str]) -> set[Name]:
        names: Set[Name] = set()
        for text in texts:
            for name in names:
                if name in text:
                    names.add(Name(id=None, value=name))
        return names