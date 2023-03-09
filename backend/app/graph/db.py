from typing import List

from app.graph.blocks import Document
from neo4j import GraphDatabase


class db:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        with self.driver:
            self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def create_documents(self, documents: List[Document]):
        with self.driver.session(database='neo4j') as session:
            result = session.execute_write(self._create_document, documents)
        print(result)

    @staticmethod
    def _create_document(tx, documents: List[Document]):
        if not documents or len(documents) < 1:
            return None
        
        neo4j_documents = [documents.to_neo4j_map() for documents in documents]

        query = (
            'UNWIND $documents as document'
            'MERGE (d: Document {id: document.id})'
            'ON CREATE'
                'SET d.integration = document.integration, d.timestamp = document.timestamp'
            'ON MATCH'
                'SET d.timestamp = document.timestamp'
                'WITH d, document'
                'CALL {'
                    'MATCH (d)-[]-(dc: Chunk)'
                    'DETACH DELETE dc'
                '}' 
            'WITH document, d'
            'UNWIND document.chunks as chunk'
            'MERGE (c: Chunk {id: chunk.id})'
            'ON CREATE'
                'SET c.text = chunk.text, c.type = chunk.type, c.timestamp = chunk.timestamp'
            'ON MATCH'
                'SET c.text = chunk.text, c.type = chunk.type, c.timestamp = chunk.timestamp'
            'WITH c, d, chunk'
            'MERGE (c)<-[:CONSISTS_OF]-(d)'
            'WITH chunk, c'
            'UNWIND chunk.propernouns as propernoun'
            'MERGE (p: ProperNoun {id: propernoun.id})'
            'ON CREATE'
                'SET p.type = propernoun.type, p.timestamp = propernoun.timestamp'
            'ON MATCH'
                'SET p.type = propernoun.type, p.timestamp = propernoun.timestamp'
            'WITH c, p'
            'MERGE (p)<-[:REFERENCES]-(c)'
        )

        result = tx.run(query, documents=neo4j_documents)
        print(result)
        return result
        
        
    
    CONSTRAINTS = '''
    CREATE CONSTRAINT document_uniqueness IF NOT EXISTS
    FOR (d:Document) 
    REQUIRE (d.id) IS UNIQUE;

    CREATE CONSTRAINT chunk_uniqueness IF NOT EXISTS
    FOR (c:Chunk)
    REQUIRE (c.id) IS UNIQUE;

    CREATE CONSTRAINT document_id_existence IF NOT EXISTS
    FOR (d:Document)
    REQUIRE (d.id) IS NOT NULL;

    CREATE CONSTRAINT document_integration_existence IF NOT EXISTS
    FOR (d:Document)
    REQUIRE (d.integration) IS NOT NULL;

    CREATE CONSTRAINT document_timestamp_existence IF NOT EXISTS
    FOR (d:Document)
    REQUIRE (d.timestamp) IS NOT NULL;
    '''