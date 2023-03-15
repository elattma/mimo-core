from typing import Any, List

from app.graph.blocks import Chunk, Document, Entity, QueryFilter
from neo4j import GraphDatabase


class GraphDB:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_entities(self, entities: List[Entity], documents: List[Document], owner: str, timestamp: int):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._create_entities, entities, documents, owner, timestamp=timestamp)
        return result
    
    @staticmethod
    def _get_document_merge():
        merge_object = ', '.join([f'{key}: document.{key}' for key in (Document.get_index_keys())]) + ', owner: $owner'
        index_properties = Document.get_index_properties()
        if index_properties and len(index_properties) > 0:
            set_object = ', '.join([f'd.{key} = document.{key}' for key in (Document.get_index_properties())]) + ', d.timestamp = $timestamp'
        else:
            set_object = 'd.timestamp = $timestamp'
        return (
            f'MERGE (d: Document {{{merge_object}}}) '
            'ON CREATE '
                f'SET {set_object} '
            'ON MATCH '
                f'SET {set_object} '
                'WITH d, document '
                'CALL { '
                    'WITH d '
                    'MATCH (d)-[]-(c: Chunk) '
                    'DETACH DELETE c '
                '} ' 
        )
    
    @staticmethod
    def _get_chunk_merge():
        merge_object = ', '.join([f'{key}: chunk.{key}' for key in (Chunk.get_index_keys())]) + ', owner: $owner'
        set_object = ', '.join([f'c.{key} = chunk.{key}' for key in (Chunk.get_index_properties())]) + ', c.timestamp = $timestamp'
        return (
            f'MERGE (c: Chunk {{{merge_object}}}) '
            'ON CREATE '
                f'SET {set_object} '
            'ON MATCH '
                f'SET {set_object} '
            'WITH c, d, chunk '
            'MERGE (c)<-[:CONSISTS_OF]-(d) '
        )
    
    @staticmethod
    def _get_entity_merge():
        predicate_merge = 'text: predicate.text, document: predicate.document'
        subject_merge = ', '.join([f'{key}: entity.{key}' for key in (Entity.get_index_keys())]) + ', owner: $owner'
        object_merge = ', '.join([f'{key}: predicate.target.{key}' for key in (Entity.get_index_keys())]) + ', owner: $owner'
        set_object = 'p.chunk=predicate.chunk, p.id=predicate.id'
        return (
            'UNWIND $entities as entity '
            'WITH entity '
            'UNWIND entity.predicates as predicate '
            f'MERGE (s:Entity {{{subject_merge}}}) '
            'WITH s, predicate '
            f'MERGE (o:Entity {{{object_merge}}}) '
            'WITH s, o, predicate '
            f'MERGE (s)-[p:Predicate {{{predicate_merge}}}]->(o) '
            'ON CREATE '
                f'SET {set_object} '
            'ON MATCH '
                f'SET {set_object} '
        )

    @staticmethod
    def _create_entities(tx, entities: List[Entity], documents: List[Document], owner: str, timestamp: int):
        if not (entities and len(entities) > 0 and documents and len(documents) > 0):
            return None
        
        neo4j_documents = [document.to_neo4j_map() for document in documents]
        documents_query = (
            'UNWIND $documents as document '
            f'{GraphDB._get_document_merge()}'
            'WITH document, d '
            'CALL { '
                'WITH d '
                'MATCH ()-[p:Predicate {document: d.id}]-() '
                'DELETE p '
            '} '
            'UNWIND document.chunks as chunk '
            f'{GraphDB._get_chunk_merge()} '
        )
        documents_result = tx.run(documents_query, documents=neo4j_documents,timestamp=timestamp, owner=owner)
        print(documents_result)

        print('hey')
        print(entities)
        neo4j_entities = [entity.to_neo4j_map() for entity in entities]
        print(neo4j_entities)
        entities_result = tx.run(GraphDB._get_entity_merge(), entities=neo4j_entities, timestamp=timestamp, owner=owner)
        print(entities_result)
        return entities_result

    def get_chunks(self, query_filter: QueryFilter) -> Any:
        with self.driver.session(database='neo4j') as session:
            result = session.read_transaction(self._get_chunks_by_filter, query_filter)
        return result

    @staticmethod
    def _get_chunks_by_filter(tx, query_filter: QueryFilter) -> List[Chunk]:
        if not query_filter or not query_filter.owner:
            return None
        
        query_wheres = []
        if query_filter.owner:
            query_wheres.append('d.owner = owner, c.owner = owner, p.owner = owner')
        
        if query_filter.document_filter:
            if query_filter.document_filter.ids:
                query_wheres.append(f'd.id IN {query_filter.document_filter.ids}')
            if query_filter.document_filter.integrations:
                query_wheres.append(f'd.integration IN {query_filter.document_filter.integrations}')

        if query_filter.chunk_filter:
            if query_filter.chunk_filter.ids:
                query_wheres.append(f'c.id IN {query_filter.chunk_filter.ids}')
            if query_filter.chunk_filter.types:
                query_wheres.append(f'c.type IN {query_filter.chunk_filter.types}')
                
        if query_filter.propernoun_filter:
            if query_filter.propernoun_filter.ids:
                query_wheres.append(f'p.id IN {query_filter.propernoun_filter.ids}')
            if query_filter.propernoun_filter.types:
                query_wheres.append(f'p.type IN {query_filter.propernoun_filter.types}')

        if len(query_wheres) < 1:
            return None

        query = (
            'MATCH (d: Document)-[co:CONSISTS_OF]->(c: Chunk)-[r:REFERENCES]->(p: ProperNoun) '
            f'WHERE {", ".join(query_wheres)} '
            'RETURN d, c, p, co, r '
        )
        return tx.run(query, owner=query_filter.owner)