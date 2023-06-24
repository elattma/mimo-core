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
        'CREATE CONSTRAINT block_uniqueness IF NOT EXISTS FOR (b:Block) REQUIRE (b.library, b.id) IS NODE KEY; ',
        'CREATE CONSTRAINT entity_uniqueness IF NOT EXISTS FOR (e:Entity) REQUIRE (e.library, e.id) IS NODE KEY; ',
        'CREATE RANGE INDEX entity_value_index IF NOT EXISTS FOR (e:Entity) ON (e.library, e.value); '
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
    # setup_neo4j()
    # setup_pinecone('beta', 'us-east1-gcp', ['library', 'date_day', 'block_label', 'page_type'])
    pass