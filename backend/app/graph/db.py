from typing import Any, List

from app.graph.blocks import Chunk, Document, QueryFilter
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
            result = session.execute_write(self._create_document, documents, user, timestamp=timestamp)
        print(result)

    @staticmethod
    def _create_document(tx, documents: List[Document], user: str, timestamp: int):
        if not documents or len(documents) < 1:
            return None
        
        neo4j_documents = [document.to_neo4j_map() for document in documents]
        print(neo4j_documents)

        query = (
            'UNWIND $documents as document '
            'MERGE (d: Document {id: document.id, integration: document.integration, user: $user}) '
            'ON CREATE '
                'SET d.timestamp = $timestamp '
            'ON MATCH '
                'SET d.timestamp = $timestamp '
                'WITH d, document '
                'CALL { '
                    'WITH d '
                    'MATCH (d)-[]-(dc: Chunk) '
                    'DETACH DELETE dc '
                '} ' 
            'WITH document, d '
            'UNWIND document.chunks as chunk '
            'MERGE (c: Chunk {id: chunk.id, user: $user}) '
            'ON CREATE '
                'SET c.content = chunk.content, c.type = chunk.type, c.timestamp = $timestamp '
            'ON MATCH '
                'SET c.content = chunk.content, c.type = chunk.type, c.timestamp = $timestamp '
            'WITH c, d, chunk '
            'MERGE (c)<-[:CONSISTS_OF]-(d) '
            'WITH chunk, c '
            'UNWIND chunk.propernouns as propernoun '
            'MERGE (p: ProperNoun {id: propernoun.id, user: $user}) '
            'ON CREATE '
                'SET p.type = propernoun.type, p.timestamp = $timestamp '
            'ON MATCH '
                'SET p.type = propernoun.type, p.timestamp = $timestamp '
            'WITH c, p '
            'MERGE (p)<-[:REFERENCES]-(c) '
        )

        result = tx.run(query, documents=neo4j_documents, timestamp=timestamp, user=user)
        print(result)
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