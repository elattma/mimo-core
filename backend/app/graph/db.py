from typing import Any, List

from app.graph.blocks import Chunk, Document, Entity, EntityFilter, QueryFilter
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
            result = session.execute_write(
                self._create_entities, entities, documents, owner, timestamp=timestamp)
            return result

    @staticmethod
    def _get_document_merge():
        merge_object = ', '.join([f'{key}: document.{key}' for key in (
            Document.get_index_keys())]) + ', owner: $owner'
        index_properties = Document.get_index_properties()
        if index_properties and len(index_properties) > 0:
            set_object = ', '.join([f'd.{key} = document.{key}' for key in (
                Document.get_index_properties())]) + ', d.timestamp = $timestamp'
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
        merge_object = ', '.join([f'{key}: chunk.{key}' for key in (
            Chunk.get_index_keys())]) + ', owner: $owner'
        set_object = ', '.join([f'c.{key} = chunk.{key}' for key in (
            Chunk.get_index_properties())]) + ', c.timestamp = $timestamp'
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
        subject_merge = ', '.join([f'{key}: entity.{key}' for key in (
            Entity.get_index_keys())]) + ', owner: $owner'
        object_merge = ', '.join([f'{key}: predicate.target.{key}' for key in (
            Entity.get_index_keys())]) + ', owner: $owner'
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
        documents_result = tx.run(
            documents_query, documents=neo4j_documents, timestamp=timestamp, owner=owner)
        neo4j_entities = [entity.to_neo4j_map() for entity in entities]
        entities_result = tx.run(GraphDB._get_entity_merge(
        ), entities=neo4j_entities, timestamp=timestamp, owner=owner)
        return list(entities_result) + list(documents_result)

    def get_by_filter(self, query_filter: QueryFilter) -> Any:
        with self.driver.session(database='neo4j') as session:
            result = session.execute_read(self._get_by_filter, query_filter)
            return result

    @staticmethod
    def _get_by_filter(tx, query_filter: QueryFilter) -> List[Chunk]:
        if not query_filter or not query_filter.owner:
            return None

        document_query_wheres = []
        entity_query_wheres = []
        if query_filter.owner:
            document_query_wheres.append(
                'd.owner = $owner AND c.owner = $owner')
            entity_query_wheres.append('s.owner = $owner AND o.owner = $owner')

        if query_filter.document_filter:
            document_filter = query_filter.document_filter
            if document_filter.ids:
                document_query_wheres.append(
                    f'd.id IN {list(document_filter.ids)}')
            if document_filter.integrations:
                document_query_wheres.append(
                    f'(d.integration IN {list(document_filter.integrations)})')
            if document_filter.time_range:
                document_query_wheres.append(
                    f'(d.timestamp >= {document_filter.time_range[0]} AND d.timestamp <= {document_filter.time_range[1]})')

        if query_filter.chunk_filter:
            chunk_filter = query_filter.chunk_filter
            if chunk_filter.ids:
                document_query_wheres.append(
                    f'(c.id IN {list(chunk_filter.ids)})')
            if chunk_filter.heights:
                document_query_wheres.append(
                    f'(c.height IN {list(chunk_filter.heights)})')
            if chunk_filter.time_range:
                document_query_wheres.append(
                    f'(d.timestamp >= {chunk_filter.time_range[0]} AND d.timestamp <= {chunk_filter.time_range[1]})')

        if query_filter.entity_filter:
            entity_filter = query_filter.entity_filter
            if entity_filter.ids:
                entity_query_wheres.append(
                    f'(s.id IN {list(entity_filter.ids)} OR o.id IN {list(entity_filter.ids)})')
            if entity_filter.types:
                entity_query_wheres.append(
                    f'(s.types IN {list(entity_filter.types)} OR o.types IN {list(entity_filter.types)})')

        if query_filter.predicate_filter:
            predicate_filter = query_filter.predicate_filter
            if predicate_filter.ids:
                entity_query_wheres.append(
                    f'(p.id IN {list(predicate_filter.ids)})')
            if predicate_filter.texts:
                entity_query_wheres.append(
                    f'(p.types IN {list(predicate_filter.texts)})')

        if len(document_query_wheres) + len(entity_query_wheres) < 1:
            return None

        query = ''
        has_document_query = len(document_query_wheres) > 1
        has_entity_query = len(entity_query_wheres) > 1
        if has_document_query:
            query += (
                'MATCH (d: Document)-[co:CONSISTS_OF]->(c: Chunk) '
                f'WHERE {" AND ".join(document_query_wheres)} '
            )
            if has_entity_query:
                query += 'WITH d, co, c '

        if has_entity_query:
            query += (
                'MATCH (s: Entity)-[p:Predicate]->(o: Entity) '
                f'WHERE {" AND ".join(entity_query_wheres)} '
            )
        if not query:
            return None

        query += 'RETURN '
        if has_document_query:
            query += 'd, co, c'
            if has_entity_query:
                query += ', '
        if has_entity_query:
            query += 's, p, o'
        result = tx.run(query, owner=query_filter.owner)
        return list(result)
