import json
import os
from typing import Dict, List

from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from util.ingestor import Ingest, Ingestor
from util.response import Errors
from util.secrets import Secrets

_ingestor: Ingestor = None

def handler(event: dict, context):
    global _ingestor

    stage: str = os.getenv('STAGE')
    graph_db_uri: str = os.getenv('GRAPH_DB_URI')
    library: str = event.get('library', None) if event else None
    connection: str = event.get('connection', None) if event else None
    integration: str = event.get('integration', None) if event else None
    s3_blocks: Dict = event.get('s3_blocks', None) if event else None
    s3_blocks: List[str] = json.loads(s3_blocks) if s3_blocks else None
    s3_pages: Dict = event.get('s3_pages', None) if event else None
    s3_pages: List[str] = json.loads(s3_pages) if s3_pages else None

    if not (stage and graph_db_uri and library and connection and integration and s3_blocks and s3_pages):
        return {
            'error': Errors.MISSING_PARAMS.value
        }

    if not _ingestor:
        secrets = Secrets(stage)
        _ingestor = Ingestor(
            openai=OpenAI(api_key=secrets.get('OPENAI_API_KEY')),
            neo4j=Neo4j(
                uri=graph_db_uri,
                user=secrets.get('GRAPH_DB_KEY'),
                password=secrets.get('GRAPH_DB_SECRET'),
            ),
            pinecone=Pinecone(
                api_key=secrets.get('PINECONE_API_KEY'), environment='us-east1-gcp'
            )
        )

    
    ingests: List[Ingest] = []
    ingests.append(Ingest(
        library=library,
        page_id='some_id',
        connection=connection,
        integration='some_integration',
        block_streams=[]
    ))

    return {
        'success': True
    }

