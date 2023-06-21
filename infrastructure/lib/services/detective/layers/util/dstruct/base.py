from typing import Set

from dstruct.dao import DStructDao
from dstruct.graphdb import GraphDB
from dstruct.model import Block, Entity
from dstruct.vectordb import VectorDB


class DStruct:
    def __init__(self, graphdb: GraphDB, vectordb: VectorDB, library: str):
        self._graphdb = graphdb
        self._vectordb = vectordb
        self._dao = DStructDao(library=library)

    def merge(self,
              block: Block,
              entities: Set[Entity] = None,
              adjacent_block_ids: Set[str] = None,
              inferrable_entity_values: Set[str] = None) -> bool:
        if not (block and block.is_valid()):
            return False
        
        graph_node = self._dao.block_to_node(block, adjacent_block_ids)
        block_row = self._dao.block_to_row(block)
        block_chunk_rows = self._dao.block_chunks_to_rows(block)
        entity_nodes = []
        if entities:
            entity_nodes = [self._dao.entity_to_node(entity, [block.id]) for entity in entities]

        self._graphdb.add_blocks([graph_node])
        self._graphdb.add_entities(entity_nodes)
        self._vectordb.upsert([block_row] + block_chunk_rows if block_chunk_rows else [block_row])

        return True
    