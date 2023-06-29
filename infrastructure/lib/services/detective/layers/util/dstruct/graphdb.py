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
        return set(['label', 'connection', 'integration', 'properties', 'last_updated_timestamp'])
    
    def add_blocks(self, blocks: List[Node]):
        if not blocks:
            raise ValueError('[GraphDB.add_blocks] blocks must not be empty')
        for block in blocks:
            if not (block.library and block.id and block.data):
                raise ValueError('[GraphDB.add_blocks] nodes must have library, id, and data')
            
            if self._block_data_keys.difference(block.data.keys()):
                raise ValueError(f'[GraphDB.add_blocks] block data must have {self._block_data_keys} but only has {block.data.keys()}')

        return self._db.write(self._add_blocks_cypher(self._block_data_keys), blocks=[self._node_to_dict(block) for block in blocks])
    
    def clean_adjacent_blocks(self, library: str, connection: str):
        return self._db.write(self._clean_adjacent_blocks_cypher(), library=library, connection=connection)

    @property
    def _entity_data_keys(self) -> Set[str]:
        return set(['identifiables'])

    def add_entities(self, entities: List[Node]):
        if not entities:
            raise ValueError('[GraphDB.add_entities] entities must not be empty')
        for entity in entities:
            if not (entity.library and entity.id and entity.data):
                raise ValueError('[GraphDB.add_entities] nodes must have library, id, and data')
            
            if self._entity_data_keys.difference(entity.data.keys()):
                raise ValueError(f'[GraphDB.add_entities] block data must have {self._block_data_keys} but only has {entity.data.keys()}')

        return self._db.write(self._add_entities_cypher(), entities=[self._node_to_dict(entity) for entity in entities])
    
    def _record_to_node(self, record) -> Node:
        record_block = record['block']
        return Node(
            library=record_block['library'],
            id=record_block['id'],
            data={
                'label': record_block['label'],
                'connection': record_block['connection'],
                'integration': record_block['integration'],
                'properties': record_block['properties'],
                'last_updated_timestamp': record_block['last_updated_timestamp'],
            }
        )

    def query_blocks(self, end: BlockQuery, library: str, start: BlockQuery = None) -> List[Node]:
        if not (end and library):
            raise ValueError(f'[GraphDB.query_blocks] end {end} and library {library} must not be empty')

        records = self._db.read(query=self._query_blocks_cypher(end, start), library=library)
        return [self._record_to_node(record) for record in records] if records else []
    
    def query_by_ids(self, ids: List[str], library: str) -> List[Node]:
        if not (ids and library):
            raise ValueError(f'[GraphDB.query_by_ids] ids {ids} and library {library} must not be empty')

        records = self._db.read(query=self._query_ids_cypher(), ids=ids, library=library)
        return [self._record_to_node(record) for record in records] if records else []
    
    def get_labels(self, library: str) -> List[str]:
        if not library:
            raise ValueError(f'[GraphDB.get_labels] library {library} must not be empty')

        query = (
            'MATCH (b: Block {library: $library}) '
            'RETURN DISTINCT b.label as label '
        )

        records = self._db.read(query, library=library)
        labels: List[str] = []
        for record in records:
            if record['label']:
                labels.append(record['label'])
        return labels

    def _node_index_match(self, name: str):
        return ', '.join([f'{key}: {name}.{key}' for key in Node.get_index_keys()])

    def _add_blocks_cypher(self, property_keys: Set[str]) -> str:
        set_object = ', '.join([f'b.{key} = CASE WHEN block.{key} IS NOT NULL THEN block.{key} ELSE b.{key} END' for key in property_keys])
        return (
            'UNWIND $blocks as block '
            f'MERGE (b: Block {{{self._node_index_match("block")}}}) '
            f'ON CREATE SET {set_object} '
            f'ON MATCH SET {set_object} '
            'WITH b, block '
            'UNWIND block.relationships as adjacent_block '
            f'MERGE (ab: Block {{{self._node_index_match("adjacent_block")}, connection: block.connection }}) '
            'WITH b, ab '
            'MERGE (b)-[:Has]->(ab) '
        )
    
    def _clean_adjacent_blocks_cypher(self) -> str:
        return (
            'MATCH (block: Block {library: $library, connection: $connection}) '
            'WHERE block.label IS NULL OR block.properties IS NULL OR block.last_updated_timestamp IS NULL '
            'DETACH DELETE block '
        )

    # TODO: merge entities on identifiables like this:
    # 'UNWIND $entities as entity '
    # 'OPTIONAL MATCH (e: Entity) '
    # 'WHERE toLower(e.id) CONTAINS toLower(entity.id) OR toLower(entity.id) CONTAINS toLower(e.id) '
    # 'OR ANY(iden IN entity.identifiables WHERE iden IN e.identifiables) '
    # 'WITH entity, e '
    # 'CALL apoc.do.when(size(entity.identifiables) > 0 AND e IS NULL, '
    # f'"MERGE (merged_e:Entity {{{self._node_index_match("entity")}, identifiables: entity.identifiables}}) RETURN merged_e", "", {{entity:entity}}) YIELD value ' 
    # 'WITH entity, e, value.merged_e as merged_e '
    # 'FOREACH(ignore_me IN CASE WHEN size(entity.identifiables) > 0 AND e IS NOT NULL THEN [1] ELSE [] END | '
    # 'SET e.identifiables = apoc.coll.toSet(e.identifiables + entity.identifiables)'
    # ') '
    # 'WITH entity, CASE WHEN e IS NULL THEN merged_e ELSE e END AS merged_e, CASE WHEN merged_e IS NOT NULL OR e IS NOT NULL THEN entity.relationships ELSE [] END AS relationships '
    # 'UNWIND relationships AS block '
    # f'MATCH (b: Block {{{self._node_index_match("block")}}}) '
    # 'WITH merged_e, b '
    # 'MERGE (merged_e)-[:Mentioned]->(b) '
    def _add_entities_cypher(self) -> str:
        return (
            'UNWIND $entities as entity '
            f'MERGE (e: Entity {{{self._node_index_match("entity")}}}) '
            'ON MATCH SET e.identifiables = apoc.coll.toSet(e.identifiables + entity.identifiables) '
            'ON CREATE SET e.identifiables = entity.identifiables '
            'WITH e, entity '
            'UNWIND entity.relationships as block '
            f'MATCH (b: Block {{{self._node_index_match("block")}}}) '
            'WITH e, b '
            'MERGE (e)-[:Mentioned]->(b)'
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
            contains_id = []
            for entity in block_query.entities:
                contains_id.append(f'toLower(entity.id) CONTAINS "{entity.lower()}"')
            where_filters.append(f'({" OR ".join(contains_id)})')
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
        start_end_match = ', start MATCH (start)-[:Has*]-(end) WITH DISTINCT end' if start else ''

        end_query = (
            'MATCH (entity: Entity)-[:Mentioned]->(end: Block) '
            f'WHERE {" AND ".join(end_where)} '
            'WITH DISTINCT end'
            f'{start_end_match} '
            'RETURN end AS block '
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