# Beware, each operation needs to be idempotent
import os
from typing import List

import dotenv

dotenv.load_dotenv('./secrets.env')

def setup_pinecone(index_name: str, environment: str, metadata_keys: List[str], dimension: int = 1536):
    import pinecone
    pinecone.init(api_key=os.environ['PINECONE_API_KEY'], environment=environment)
    indexes = pinecone.list_indexes()
    if index_name in indexes:
        return

    pinecone.create_index(
        name=index_name,
        metadata_config={
            'indexed': metadata_keys
        },
        dimension=dimension,
    )

def _get_constraints() -> List[str]:
    return [
        'CREATE CONSTRAINT page_uniqueness IF NOT EXISTS FOR (p:Page) REQUIRE (p.library, p.id) IS NODE KEY; ',
        'CREATE CONSTRAINT page_connection_existence IF NOT EXISTS FOR (p:Page) REQUIRE (p.connection) IS NOT NULL; ',
        'CREATE CONSTRAINT page_type_existence IF NOT EXISTS FOR (p:Page) REQUIRE (p.type) IS NOT NULL; ',
        'CREATE CONSTRAINT page_lut_existence IF NOT EXISTS FOR (p:Page) REQUIRE (p.last_updated_timestamp) IS NOT NULL; ',
        'CREATE CONSTRAINT page_summary_existence IF NOT EXISTS FOR (p:Page) REQUIRE (p.summary) IS NOT NULL; ',
        'CREATE CONSTRAINT block_uniqueness IF NOT EXISTS FOR (b:Block) REQUIRE (b.library, b.id) IS NODE KEY; ',
        'CREATE CONSTRAINT block_label_existence IF NOT EXISTS FOR (b:Block) REQUIRE (b.label) IS NOT NULL; ',
        'CREATE CONSTRAINT block_lut_existence IF NOT EXISTS FOR (b:Block) REQUIRE (b.last_updated_timestamp) IS NOT NULL; ',
        'CREATE CONSTRAINT block_blocks_existence IF NOT EXISTS FOR (b:Block) REQUIRE (b.blocks) IS NOT NULL; ',
        'CREATE CONSTRAINT name_uniqueness IF NOT EXISTS FOR (n:Name) REQUIRE (n.library, n.id) IS NODE KEY; ',
        'CREATE RANGE INDEX name_value_index IF NOT EXISTS FOR (n:Name) ON (n.library, n.value); '
    ]

def setup_neo4j():
    from neo4j import GraphDatabase
    uri = os.environ['NEO4J_URI']
    user = os.environ['NEO4J_USER']
    password = os.environ['NEO4J_PASSWORD']
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session(database='neo4j') as session:
        for constraint in _get_constraints():
            session.run(constraint)

    driver.close()

if __name__ == '__main__':
    setup_neo4j()
    setup_pinecone('beta', 'us-east1-gcp', ['library', 'date_day', 'block_label', 'page_type'])
    pass