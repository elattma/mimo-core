from logging import getLogger
from typing import Dict, List, Set

from dstruct.dao import DStructDao
from dstruct.graphdb import GraphDB
from dstruct.model import Block, BlockQuery, Entity
from dstruct.vectordb import Row, VectorDB

_logger = getLogger('DStruct')

class DStruct:
    def __init__(self, graphdb: GraphDB, vectordb: VectorDB, library: str, log_level: int):
        self._graphdb = graphdb
        self._vectordb = vectordb
        self._library = library
        self._dao = DStructDao(library=library, log_level=log_level)

        _logger.setLevel(log_level)

    def merge(self, block: Block, entities: List[Entity] = None, adjacent_block_ids: Set[str] = None) -> None:
        graph_node = self._dao.block_to_node(block, adjacent_block_ids)
        block_row = self._dao.block_to_row(block)
        block_chunk_rows = self._dao.block_chunks_to_rows(block)
        entity_nodes = [self._dao.entity_to_node(entity, [block.id]) for entity in entities] if entities else []

        self._graphdb.add_blocks([graph_node])
        self._vectordb.upsert([block_row] + block_chunk_rows if block_chunk_rows else [block_row])
        if entity_nodes:
            self._graphdb.add_entities(entity_nodes)
        _logger.debug(f'[merge] merged block {str(block.id)} with {len(block.properties)} properties entities {str(entities)} adjacent_block_ids {str(adjacent_block_ids)}')
    
    def clean_adjacent_blocks(self, connection: str) -> None:
        self._graphdb.clean_adjacent_blocks(self._library, connection)
    
    def _blocks_with_embeddings(self, blocks: List[Block]) -> None:
        id_to_block: Dict[str, Block] = {}
        for block in blocks:
            id_to_block[block.id] = block

        rows: List[Row] = self._vectordb.fetch(list(id_to_block.keys()), self._library)
        for row in rows:
            id_to_block[row.id].embedding = row.embedding

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
                _logger.debug(f'[query] exact query {start} -> {end}')
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                _logger.debug(f'[query] found nodes in neo4j {str(nodes)}')
                if not nodes:
                    return None

                blocks = [self._dao.node_to_block(node) for node in nodes]
            elif start.search_method == 'relevant':
                _logger.debug(f'[query] relevant then exact query {start} -> {end}')
                rows: List[Row] = self._vectordb.query(
                    block_query=start,
                    library=self._library,
                    top_k=1000,
                    include_values=False,
                    type='block'
                )
                _logger.debug(f'[query] found rows in pinecone {str(rows)}')

                if not rows:
                    return None
                start.ids = [row.id for row in rows]
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                _logger.debug(f'[query] found nodes in neo4j {str(nodes)}')
                if not nodes:
                    return None
                
                blocks = [self._dao.node_to_block(node) for node in nodes]
        elif end.search_method == 'relevant':
            if not start:
                _logger.debug(f'[query] relevant query {end}')
                rows = self._vectordb.query(
                    block_query=end,
                    library=self._library,
                    top_k=end.limit if end.limit else 5,
                    include_values=True,
                    type='block'
                )
                row_ids = [row.id for row in rows]
                _logger.debug(f'[query] found rows in pinecone {str(row_ids)}')
                nodes = self._graphdb.query_by_ids(row_ids, self._library)
                _logger.debug(f'[query] found nodes in neo4j {str(nodes)}')
                if not nodes:
                    return None
                blocks = [self._dao.node_to_block(node) for node in nodes]
            elif start.search_method == 'exact':
                _logger.debug(f'[query] exact then relevant query {start} -> {end}')
                nodes = self._graphdb.query_blocks(end=end, library=self._library, start=start)
                if not nodes:
                    return None
                blocks = [self._dao.node_to_block(node) for node in nodes]
                # TODO: rerank with cohere ai?
            elif start.search_method == 'relevant':
                _logger.debug(f'[query] relevant then relevant query {start} -> {end}')
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
                # TODO: rerank with cohere ai?

        if blocks:
            if with_data and not blocks[0].properties:
                self._blocks_with_data(blocks)
            if with_embeddings and not blocks[0].embedding:
                self._blocks_with_embeddings(blocks)
            _logger.debug(f'[query] found blocks {str(blocks)}')
            return blocks
        
        _logger.debug(f'[query] no blocks found')
        return None
  