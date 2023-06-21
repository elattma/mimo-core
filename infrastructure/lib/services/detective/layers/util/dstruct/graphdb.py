from dataclasses import dataclass
from typing import Any, Dict, List, Literal

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
    
    def as_dict(self):
        return {
            'library': self.library,
            'id': self.id
        }

@dataclass
class Node(Identifiable):
    data: Dict[str, Any]
    relationships: List['Relationship'] = None

    def as_dict(self):
        as_dict = super().as_dict()
        as_dict.update(**(self.data if self.data else {}))
        as_dict['relationships'] = [relationship.as_dict() for relationship in self.relationships] if self.relationships else None

        return as_dict
    

@dataclass
class Relationship(Identifiable):
    type: Literal['Mentioned', 'Has']

    def as_dict(self):
        as_dict = super().as_dict()
        as_dict['type'] = self.type
        return as_dict


class GraphDB:
    def __init__(self, db: Neo4j) -> None:
        self._db = db

    def _validate_nodes(self, nodes: List[Node]):
        if not nodes:
            raise ValueError('nodes must not be empty')
        for node in nodes:
            if not node.library or not node.id:
                raise ValueError('node must have library and id')

    def add_blocks(self, nodes: List[Node]):
        self._validate_nodes(nodes)
        return self._db.write(self._add_blocks_cypher, nodes)

    def add_entities(self, nodes: List[Node]):
        self._validate_nodes(nodes)
        return self._db.write(self._add_entities_cypher, nodes)
    
    def _node_merge_object(self, name: str):
        return ', '.join([f'{key}: {name}.{key}' for key in Node.get_index_keys()])

    @property
    def _add_blocks_cypher(self):
        return (
            'UNWIND $blocks as block '
            f'MERGE (b: Block {{{self._node_merge_object("block")}}}) '
            'ON CREATE '
            f'SET b.data = block.data '
            'ON MATCH '
            f'SET b.data = block.data '
        )

    @property
    def _add_entities_cypher(self):
        return (
            'UNWIND $entities as entity '
            f'MERGE (e: Entity {{{self._node_merge_object("entity")}}}) '
            'ON CREATE '
            f'SET e.data = entity.data '
            'WITH e, entity '
            'UNWIND entity.relationships as block '
            f'MATCH (b: Block {{{self._node_merge_object("block")}}}) '
            'WITH e, b '
            'MERGE (e)-[:Mentioned]->(b) '
        )
