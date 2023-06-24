from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Set

from dstruct.model import BlockQuery
from external.neo4j_ import Neo4j


@dataclass
class Identifiable:
    library: str
    id: str

    @staticmethod
    def get_index_keys():
        return ['library', 'id']
    
    def __hash__(self):
        return hash((self.library, self.id))
    
    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.library == other.library and self.id == other.id
    

@dataclass
class Node(Identifiable):
    data: Dict[str, Any]
    relationships: List['Relationship'] = None

@dataclass
class Relationship(Identifiable):
    type: Literal['Mentioned', 'Has']


class GraphDB:
    def __init__(self, db: Neo4j) -> None:
        self._db = db
            
    def _node_to_dict(self, node: Node):
        return {
            'library': node.library,
            'id': node.id,
            **(node.data if node.data else {}),
            'relationships': [self._relationship_to_dict(relationship) for relationship in node.relationships] if node.relationships else [],
        }
    
    def _relationship_to_dict(self, relationship: Relationship):
        return {
            'library': relationship.library,
            'id': relationship.id,
            'type': relationship.type,
        }
    
    @property
    def _block_data_keys(self) -> Set[str]:
        return set('label', 'integration', 'properties', 'last_updated_timestamp')
    
    def add_blocks(self, blocks: List[Node]):
        if not blocks:
            raise ValueError('[GraphDB.add_blocks] blocks must not be empty')
        for block in blocks:
            if not (block.library and block.id and block.data):
                raise ValueError('[GraphDB.add_blocks] nodes must have library, id, and data')
            
            if self._block_data_keys.difference(block.data.keys()):
                raise ValueError(f'[GraphDB.add_blocks] block data must have {self._block_data_keys} but only has {block.data.keys()}')

        return self._db.write(self._add_blocks_cypher(self._block_data_keys), [self._node_to_dict(block) for block in blocks])

    @property
    def _entity_data_keys(self) -> Set[str]:
        return set('value', 'identifiables')

    def add_entities(self, entities: List[Node]):
        if not entities:
            raise ValueError('[GraphDB.add_entities] entities must not be empty')
        for entity in entities:
            if not (entity.library and entity.id and entity.data):
                raise ValueError('[GraphDB.add_entities] nodes must have library, id, and data')
            
            if self._entity_data_keys.difference(entity.data.keys()):
                raise ValueError(f'[GraphDB.add_entities] block data must have {self._block_data_keys} but only has {entity.data.keys()}')

        return self._db.write(self._add_entities_cypher(self._entity_data_keys), [self._node_to_dict(entity) for entity in entities])
    
    def query_blocks(self, end: BlockQuery, library: str, start: BlockQuery = None) -> List[Node]:
        if not (end and library):
            raise ValueError(f'[GraphDB.query_blocks] end {end} and library {library} must not be empty')

        return self._db.read(query=self._query_blocks_cypher(end, start), library=library)
    
    def query_by_ids(self, ids: List[str], library: str) -> List[Node]:
        if not (ids and library):
            raise ValueError(f'[GraphDB.query_by_ids] ids {ids} and library {library} must not be empty')

        return self._db.read(self._query_ids_cypher(), ids, library)
    
    def _node_index_match(self, name: str):
        return ', '.join([f'{key}: {name}.{key}' for key in Node.get_index_keys()])

    def _add_blocks_cypher(self, property_keys: Set[str]) -> str:
        set_object = ', '.join([f'b.{key} = block.{key}' for key in property_keys])
        return (
            'UNWIND $nodes as block '
            f'MERGE (b: Block {{{self._node_index_match("block")}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
            'WITH b, block '
            'UNWIND block.relationships as adjacent_block '
            f'MERGE (ab: Block {{{self._node_index_match("adjacent_block")}}}) '
            'WITH b, ab '
            'MERGE (b)-[:Has]->(ab) '
        )

    def _add_entities_cypher(self, property_keys: Set[str]) -> str:
        set_object = ', '.join([f'e.{key} = entity.{key}' for key in property_keys])
        return (
            'UNWIND $nodes as entity '
            f'MERGE (e: Entity {{{self._node_index_match("entity")}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'WITH e, entity '
            'UNWIND entity.relationships as block '
            f'MATCH (b: Block {{{self._node_index_match("block")}}}) '
            'WITH e, b '
            'MERGE (e)-[:Mentioned]->(b) '
        )
    
    # TODO: optimize by putting integrations, time, entities, and any params as injectable parameters in the driver
    def _where_filters(self, block_query: BlockQuery, name: str) -> List[str]:
        where_filters = [f'{name}.library = $library']
        if block_query.ids:
            where_filters.append(f'{name}.id IN {block_query.ids}')
        if block_query.integrations:
            where_filters.append(f'{name}.integration IN {block_query.integrations}')
        if block_query.absolute_time_start:
            start_timestamp = int(datetime.strptime(block_query.absolute_time_start, '%Y-%m-%d').timestamp())
            where_filters.append(f'{name}.last_updated_timestamp >= {start_timestamp}')
        if block_query.absolute_time_end:
            end_timestamp = int(datetime.strptime(block_query.absolute_time_end, '%Y-%m-%d').timestamp())
            where_filters.append(f'{name}.last_updated_timestamp <= {end_timestamp}')
        if block_query.labels:
            where_filters.append(f'{name}.label IN {block_query.labels}')
        if block_query.entities:
            contains_value = []
            for entity in block_query.entities:
                contains_value.append(f'toLower(entity.value) CONTAINS "{entity.lower()}"')
            where_filters.append(f'({" OR ".join(contains_value)})')
        return where_filters
    
    def _post_filters(self, block_query: BlockQuery, name: str) -> List[str]:
        post_filters = []
        if block_query.relative_time:
            post_filters.append(f'ORDER BY {name}.last_updated_timestamp {block_query.relative_time.upper()}')
        if block_query.offset:
            post_filters.append(f'SKIP {block_query.offset}')
        post_filters.append(f'LIMIT {block_query.limit if block_query.limit else 10}')

        return post_filters

    def _query_blocks_cypher(self, end: BlockQuery, start: BlockQuery = None) -> str:
        start_query = ''
        if start:
            start_where = self._where_filters(start, 'start')
            start_post = self._post_filters(start, 'start')
            start_query = (
                'MATCH (entity: Entity)-[:Mentioned]->(start: Block) '
                f'WHERE {" AND ".join(start_where)} '
                'WITH DISTINCT start '
                f'{" ".join(start_post)} '
                'WITH start '
            )

        end_where = self._where_filters(end, 'end')
        end_post = self._post_filters(end, 'end')
        start_end_match = ', start MATCH (start)-[:Has*]->(end) WITH DISTINCT end' if start else ''

        end_query = (
            'MATCH (entity: Entity)-[:Mentioned]->(end: Block) '
            f'WHERE {" AND ".join(end_where)} '
            'WITH DISTINCT end'
            f'{start_end_match} '
            'RETURN end '
            f'{" ".join(end_post)}'
        )
        return start_query + end_query
    
    def _query_ids_cypher(self) -> str:
        return (
            'UNWIND $ids as id '
            'MATCH (block: Block) '
            'WHERE block.library = $library AND block.id = id '
            'RETURN block '
        )