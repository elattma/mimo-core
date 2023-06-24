from typing import Dict, List, Set

from dstruct.dao import DStructDao
from dstruct.graphdb import GraphDB
from dstruct.model import Block, BlockQuery, Entity
from dstruct.vectordb import Row, VectorDB


class DStruct:
    def __init__(self, graphdb: GraphDB, vectordb: VectorDB, library: str):
        self._graphdb = graphdb
        self._vectordb = vectordb
        self._library = library
        self._dao = DStructDao(library=library)

    def merge(self,
              block: Block,
              entities: Set[Entity] = None,
              adjacent_block_ids: Set[str] = None,
              inferrable_entity_values: Set[str] = None) -> bool:
        graph_node = self._dao.block_to_node(block, adjacent_block_ids)
        block_row = self._dao.block_to_row(block)
        block_chunk_rows = self._dao.block_chunks_to_rows(block)
        entity_nodes = []

        self._graphdb.add_blocks([graph_node])
        self._vectordb.upsert([block_row] + block_chunk_rows if block_chunk_rows else [block_row])
        if entities:
            entity_nodes = [self._dao.entity_to_node(entity, [block.id]) for entity in entities]
            self._graphdb.add_entities(entity_nodes)

        return True
    
    def _blocks_with_embeddings(self, blocks: List[Block]) -> None:
        id_to_block: Dict[str, Block] = {}
        for block in blocks:
            id_to_block[block.id] = block

        rows_map = self._vectordb.fetch(list(id_to_block.keys()), self._library)
        for id, embedding in rows_map.items():
            id_to_block[id].embedding = embedding

    def _blocks_with_data(self, blocks: List[Block]) -> None:
        id_to_block: Dict[str, Block] = {}
        for block in blocks:
            id_to_block[block.id] = block
        nodes = self._graphdb.query_by_ids(list(id_to_block.keys()), self._library)
        for node in nodes:
            node_block = self._dao.node_to_block(node)
            id_to_block[node_block.id].properties = node_block.properties

    def query(self, end: BlockQuery, start: BlockQuery = None, with_data = True, with_embeddings = True) -> List[Block]:
        blocks: List[Block] = []
        if end.search_method == 'exact':
            if not start or start.search_method == 'exact':
                print(f'[DStruct.query] exact query {start} -> {end}')
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                if not nodes:
                    return None

                blocks = [self._dao.node_to_block(node) for node in nodes]
            elif start.search_method == 'relevant':
                print(f'[DStruct.query] relevant then exact query {start} -> {end}')

                rows: Dict[str, List[float]] = self._vectordb.query(
                    block_query=start,
                    library=self._library,
                    top_k=1000,
                    include_values=False,
                    type='block'
                )
                if not rows:
                    return None
                start.ids = [block_id for block_id in rows.keys()]
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                if not nodes:
                    return None
                
                blocks = [self._dao.node_to_block(node) for node in nodes]
        elif end.search_method == 'relevant':
            if not start:
                print(f'[DStruct.query] relevant query {end}')
                rows = self._vectordb.query(
                    block_query=end,
                    library=self._library,
                    top_k=end.limit,
                    include_values=True,
                    type='block'
                )
                nodes = self._graphdb.query_by_ids(list(rows.keys()), self._library)
                if not nodes:
                    return None
                blocks = [self._dao.node_to_block(node) for node in nodes]
            elif start.search_method == 'exact':
                print(f'[DStruct.query] exact then relevant query {start} -> {end}')
                end_limit = end.limit
                end.limit = 1000
                end.relative_time_ascending = False
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                if not nodes:
                    return None
                blocks = [self._dao.node_to_block(node) for node in nodes]
                end.limit = end_limit
            elif start.search_method == 'relevant':
                print(f'[DStruct.query] relevant then relevant query {start} -> {end}')
                rows: Dict[str, List[float]] = self._vectordb.query(
                    block_query=start,
                    library=self._library,
                    top_k=1000,
                    include_values=False,
                    type='block'
                )
                if not rows:
                    return None
                start.ids = [block_id for block_id in rows.keys()]
                end_limit = end.limit
                end.limit = 1000
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                if not nodes:
                    return None
                blocks = [self._dao.node_to_block(node) for node in nodes]
                end.limit = end_limit

        if blocks:
            if with_data and not blocks[0].properties:
                self._blocks_with_data(blocks)
            if with_embeddings and not blocks[0].embedding:
                self._blocks_with_embeddings(blocks)
            return blocks
        
        return None
  