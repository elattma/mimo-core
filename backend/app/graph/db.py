from typing import Any, List

from app.graph.blocks import Chunk, Document, ProperNoun, QueryFilter
from neo4j import GraphDatabase


class GraphDB:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_documents(self, documents: List[Document], user: str, timestamp: int):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._create_documents, documents, user, timestamp=timestamp)
        return result
    
    @staticmethod
    def _get_document_merge(document: Document):
        merge_object = ', '.join([f'{key}: document.{key}' for key in (document.get_index_keys())]) + ', user: $user'
        index_properties = document.get_index_properties()
        if index_properties and len(index_properties) > 0:
            set_object = ', '.join([f'd.{key} = document.{key}' for key in (document.get_index_properties())]) + ', d.timestamp = $timestamp'
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
                    'MATCH (d)-[]-(dc: Chunk) '
                    'DETACH DELETE dc '
                '} ' 
        )
    
    @staticmethod
    def _get_chunk_merge():
        merge_object = ', '.join([f'{key}: chunk.{key}' for key in (Chunk.get_index_keys())]) + ', user: $user'
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
    def _get_propernoun_merge():
        merge_object = ', '.join([f'{key}: propernoun.{key}' for key in (ProperNoun.get_index_keys())]) + ', user: $user'
        set_object = ', '.join([f'p.{key} = propernoun.{key}' for key in (ProperNoun.get_index_properties())]) + ', p.timestamp = $timestamp'
        return (
            f'MERGE (p: ProperNoun {{{merge_object}}}) '
            'ON CREATE '
                f'SET {set_object} '
            'ON MATCH '
                f'SET {set_object} '
            'WITH c, p '
            'MERGE (p)<-[:REFERENCES]-(c) '
        )

    @staticmethod
    def _create_documents(tx, documents: List[Document], user: str, timestamp: int):
        if not documents or len(documents) < 1:
            return None
        
        query = (
            'UNWIND $documents as document '
            f'{GraphDB._get_document_merge(documents[0])}'
            'WITH document, d '
            'UNWIND document.chunks as chunk '
            f'{GraphDB._get_chunk_merge()}'
            'WITH chunk, c '
            'UNWIND chunk.propernouns as propernoun '
            f'{GraphDB._get_propernoun_merge()}'
        )

        neo4j_documents = [document.to_neo4j_map() for document in documents]
        result = tx.run(query, documents=neo4j_documents, timestamp=timestamp, user=user)
        return result

    def get_chunks(self, query_filter: QueryFilter) -> Any:
        with self.driver.session(database='neo4j') as session:
            result = session.read_transaction(self._get_chunks_by_filter, query_filter)
        return result

    @staticmethod
    def _get_chunks_by_filter(tx, query_filter: QueryFilter) -> List[Chunk]:
        if not query_filter or not query_filter.user:
            return None
        
        query_wheres = []
        if query_filter.user:
            query_wheres.append('d.user = user, c.user = user, p.user = user')
        
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
        return tx.run(query, user=query_filter.user)