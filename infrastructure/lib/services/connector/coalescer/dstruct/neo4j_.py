from dataclasses import dataclass
from typing import Any, Dict, List

from neo4j import GraphDatabase


@dataclass
class Node:
    library: str
    id: str
    properties: Dict[str, Any]
    relationships: List['Relationship'] = None

    def get_index_properties(self):
        return self.properties.keys()

    @staticmethod
    def get_index_keys():
        return ['library', 'id']
    
    def __hash__(self):
        return hash((self.library, self.id))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.library == other.library and self.id == other.id

    def get_neo4j_properties(self):
        return {
            'library': self.library,
            'id': self.id,
            **self.properties,
            'relationships': [relationship.as_dict() for relationship in self.relationships] if self.relationships else None
        }
    

@dataclass
class Relationship:
    library: str
    id: str

    def as_dict(self):
        return {
            'library': self.library,
            'id': self.id
        }


class Neo4j:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def blocks(self, blocks: List[Node]):
        if not blocks:
            raise ValueError('blocks must not be empty')
        for block in blocks:
            if not block.library or not block.id:
                raise ValueError('block must have library and id')

            if not (block.properties and 'label' in block.properties and 'last_updated_timestamp' in block.properties and 'blocks' in block.properties):
                raise ValueError('block must have label, last_updated_timestamp, and blocks')
        
        with self.driver.session(database='neo4j') as session:
            page_result = session.execute_write(self._blocks, blocks)
            return page_result
        
    def pages(self, pages: List[Node]):
        if not pages:
            raise ValueError('pages must not be empty')
        for page in pages:
            if not page.library or not page.id:
                raise ValueError('page must have library and id')

            if not (page.properties and 'connection' in page.properties and 'type' in page.properties and 'last_updated_timestamp' in page.properties and 'summary' in page.properties and page.relationships):
                raise ValueError('page must have connection, type, last_updated_timestamp, summary, and blocks')

        with self.driver.session(database='neo4j') as session:
            page_result = session.execute_write(self._pages, pages)
            return page_result
        
    def names(self, names: List[Node]):
        if not names:
            raise ValueError('names must not be empty')
        for name in names:
            if not name.library or not name.id:
                raise ValueError('name must have library and id')

            if not (name.properties and name.relationships):
                raise ValueError('name must have value')

        with self.driver.session(database='neo4j') as session:
            names_result = session.execute_write(self._names, names)
            return names_result
    
    def cleanup(self, library: str):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._cleanup, library)
            return result
        
    @staticmethod
    def _blocks(tx, blocks: List[Node]):
        neo4j_blocks = [block.get_neo4j_properties() for block in blocks]
        merge_object = ', '.join([f'{key}: block.{key}' for key in Node.get_index_keys()])
        set_object = ', '.join([f'b.{key} = block.{key}' for key in blocks[0].get_index_properties()])
        blocks_query = (
            'UNWIND $blocks as block '
            f'MERGE (b: Block {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
        )

        return list(tx.run(blocks_query, blocks=neo4j_blocks))
    
    @staticmethod
    def _pages(tx, pages: List[Node]):
        neo4j_pages = [page.get_neo4j_properties() for page in pages]
        block_merge_object = ', '.join([f'{key}: block.{key}' for key in Node.get_index_keys()])
        merge_object = ', '.join([f'{key}: page.{key}' for key in Node.get_index_keys()])
        set_object = ', '.join([f'p.{key} = page.{key}' for key in pages[0].get_index_properties()])
        print(neo4j_pages)
        pages_query = (
            'UNWIND $pages as page '
            f'MERGE (p: Page {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'ON MATCH '
            f'SET {set_object} '
            'WITH p, page '
            'CALL { '
            'WITH p, page '
            'MATCH (p)-[c:Consists]-() '
            'DETACH DELETE c '
            '} '
            'WITH p, page '
            'UNWIND page.relationships as block '
            f'MATCH (b: Block {{{block_merge_object}}}) '
            'MERGE (p)-[:Consists]->(b)'
        )

        return list(tx.run(pages_query, pages=neo4j_pages))
    
    @staticmethod
    def _names(tx, names: List[Node]):
        neo4j_names = [name.get_neo4j_properties() for name in names]
        page_merge_object = ', '.join([f'{key}: page.{key}' for key in Node.get_index_keys()])
        merge_object = ', '.join([f'{key}: name.{key}' for key in Node.get_index_keys()])
        set_object = ', '.join([f'n.{key} = name.{key}' for key in names[0].get_index_properties()])
        names_query = (
            'UNWIND $names as name '
            f'MERGE (n: Name {{{merge_object}}}) '
            'ON CREATE '
            f'SET {set_object} '
            'WITH n, name '
            'UNWIND name.relationships as page '
            f'MATCH (p: Page {{{page_merge_object}}}) '
            'WITH n, p '
            'MERGE (n)-[:Mentioned]->(p) '
        )

        return list(tx.run(names_query, names=neo4j_names))

    @staticmethod
    def _cleanup(tx, library: str):
        cleanup_query = (
            'MATCH (b: Block {library: $library}) '
            'WHERE NOT (b)-[:Consists]-() '
            'WITH b, b.id AS id '
            'DELETE b '
            'RETURN id'
        )
        result = tx.run(cleanup_query, library=library)
        records = list(result)
        return [record.get('id') for record in records]
