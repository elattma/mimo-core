import json
import os
from typing import Any, Dict, List

from context_agent.agent import ContextAgent
from context_agent.model import Request
from dstruct.base import DStruct
from dstruct.graphdb import GraphDB
from dstruct.model import Block, StructuredProperty, UnstructuredProperty
from dstruct.vectordb import VectorDB
from external.neo4j_ import Neo4j
from external.openai_ import OpenAI
from external.pinecone_ import Pinecone
from shared.response import Errors, to_response_error, to_response_success
from store.params import SSM


def handler(event: dict, context):
    global dstruct

    stage: str = os.getenv('STAGE')
    neo4j_uri: str = os.getenv('NEO4J_URI')
    app_secrets_path: str = os.getenv('APP_SECRETS_PATH')
    if not (stage and neo4j_uri and app_secrets_path):
        return to_response_error(Errors.MISSING_ENV)

    body: str = event.get('body', None) if event else None
    body: Dict = json.loads(body) if body else None
    raw_query: str = body.get('query', None) if body else None
    token_limit: int = body.get('token_limit', None) if body else None
    token_limit = int(token_limit) if token_limit else 1600
    library: str = body.get('library', 'google-oauth2|108573573074253667565') if body else None
    next_token: str = body.get('next_token', None) if body else None
    overrides: Dict[str, Any] = body.get('overrides') if body else None

    if not (raw_query and token_limit and library):
        return to_response_error(Errors.MISSING_PARAMS)
    
    secrets = SSM().load_params(app_secrets_path)
    openai_api_key = secrets.get('openai_api_key', None)
    neo4j_user = secrets.get('neo4j_user', None)
    neo4j_password = secrets.get('neo4j_password', None)
    pinecone_api_key = secrets.get('pinecone_api_key', None)
    if not (openai_api_key and neo4j_user and neo4j_password and pinecone_api_key):
        return to_response_error(Errors.MISSING_SECRETS.value)
    pinecone = Pinecone(api_key=pinecone_api_key, environment='us-east1-gcp')
    vectordb = VectorDB(db=pinecone)
    neo4j = Neo4j(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    graphdb = GraphDB(db=neo4j)
    dstruct = DStruct(graphdb=graphdb, vectordb=vectordb, library=library)
    openai = OpenAI(api_key=openai_api_key)
    context_agent = ContextAgent(dstruct=dstruct, openai=openai)
    request = Request(
        raw=raw_query,
        token_limit=token_limit,
        next_token=next_token
    )

    if overrides:
        # TODO: first validate overrides in a set of allowed overrides with allowed values
        for key, value in overrides.items():
            if hasattr(request, key):
                request.__setattr__(key, value)
            else:
                print(f'[Query] Invalid override key: {key}, value: {value}')
    blocks: List[Block] = context_agent.fetch(request)
    response = {
        'next_token': None,
    }
    response_blocks: List[Dict] = []
    if blocks:
        for block in blocks:
            block_dict = {
                'id': block.id,
                'label': block.label,
                'integration': block.integration,
                'last_updated_ts': block.last_updated_timestamp,
            }
            properties: List[Dict] = []
            for property in block.properties:
                if isinstance(property, StructuredProperty):
                    properties.append({
                        'type': 'structured',
                        'key': property.key,
                        'value': property.value if property.value else None,
                    })
                elif isinstance(property, UnstructuredProperty):
                    chunks: List[Dict] = []
                    for chunk in property.chunks:
                        chunks.append({
                            'order': chunk.order,
                            'text': chunk.text,
                        })
                    properties.append({
                        'type': 'unstructured',
                        'key': property.key,
                        'chunks': chunks
                    })
            block_dict['properties'] = properties
            response_blocks.append(block_dict)
    response['blocks'] = response_blocks

    return to_response_success(response)

