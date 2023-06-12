import json
import os
from typing import Dict

from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.context_basket.model import DataRequest
from mystery.data_agent import DataAgent
from util.openai_ import OpenAI
from util.params import SSM
from util.response import Errors, to_response_error, to_response_success


def handler(event: dict, context):
    stage: str = os.getenv('STAGE')
    graph_db_uri: str = os.getenv('GRAPH_DB_URI')
    secrets_path: str = os.getenv('SECRETS_PATH')
    body: str = event.get('body', None) if event else None
    body: Dict = json.loads(body) if body else None
    request: str = body.get('query', None) if body else None
    max_tokens: int = body.get('max_tokens', None) if body else None
    max_tokens = int(max_tokens) if max_tokens else 1600
    library: str = body.get('library', 'google-oauth2|108573573074253667565') if body else None
    next_token: str = body.get('next_token', None) if body else None
    overrides: Dict = json.loads(overrides) if overrides else None

    if not (stage and graph_db_uri and request and max_tokens and library):
        return to_response_error(Errors.MISSING_PARAMS.value)
    
    # TODO: add library config
    secrets = SSM().load_params(secrets_path)
    openai_api_key = secrets.get('openai_api_key', None)
    neo4j_user = secrets.get('neo4j_user', None)
    neo4j_password = secrets.get('neo4j_password', None)
    pinecone_api_key = secrets.get('pinecone_api_key', None)
    if not (openai_api_key and neo4j_user and neo4j_password and pinecone_api_key):
        return to_response_error(Errors.MISSING_SECRETS.value)
    pinecone = Pinecone(
        api_key=pinecone_api_key, environment='us-east1-gcp'
    )
    neo4j = Neo4j(
        uri=graph_db_uri,
        user=neo4j,
        password=neo4j_password,
    )
    openai = OpenAI(api_key=openai_api_key)
    data_agent = DataAgent(
        owner=library,
        vector_db=pinecone,
        graph_db=neo4j, 
        openai=openai, 
    )
    data_request = DataRequest(
        library=library,
        request=request,
        query=Query(),
        max_tokens=max_tokens
    )
    data_response = data_agent.generate_context(data_request)
    if not data_response:
        print(f'[Data] No response from data agent.')
        return to_response_error(Errors.OPENAI_ERROR)
    elif not data_response.successful:
        print(f'[Data] Error: {data_response.error.value}')
        return to_response_error(Errors.OPENAI_ERROR)
    
    return to_response_success({
        'contexts': [{ 
            'text': context.translated,
            'score': 1.0,
            'source': {
                'integration': context.source.integration,
                'page': context.source.page_id,
            }
        } for context in data_response.context_basket.contexts],
        'next_token': None
    })

