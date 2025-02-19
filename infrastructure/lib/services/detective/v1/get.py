import json
import logging
import os
from typing import Dict, List

from context_agent.agent import ContextAgent
from context_agent.model import ContextQuery, Request
from context_agent.reranker import Reranker
from dstruct.base import DStruct
from dstruct.graphdb import GraphDB
from dstruct.model import (Block, BlockQuery, StructuredProperty,
                           UnstructuredProperty)
from dstruct.vectordb import VectorDB
from external.cohere_ import Cohere
from external.neo4j_ import Neo4j
from external.openai_ import OpenAI
from external.pinecone_ import Pinecone
from shared.response import Errors, to_response_error, to_response_success
from store.params import SSM

_logger = logging.getLogger('ContextRetriever')
logging.basicConfig(level=logging.INFO)
log_level = os.getenv('LOG_LEVEL')
log_level = logging.getLevelName(log_level) if log_level else logging.DEBUG
_logger.setLevel(log_level)

def handler(event: dict, context):
    global dstruct, _logger

    stage: str = os.getenv('STAGE')
    neo4j_uri: str = os.getenv('NEO4J_URI')
    app_secrets_path: str = os.getenv('APP_SECRETS_PATH')
    if not (stage and neo4j_uri and app_secrets_path):
        _logger.exception(Errors.MISSING_ENV.value)
        return to_response_error(Errors.MISSING_ENV)

    body: str = event.get('body', None) if event else None
    body: Dict = json.loads(body) if body else None
    context_query: str = body.get('query', None) if body else None
    token_limit: str = body.get('token_limit', None) if body else None
    token_limit: int = int(token_limit) if token_limit else None
    library: str = body.get('library', None) if body else None
    next_token: str = body.get('next_token', None) if body else None

    if not (context_query and library):
        _logger.exception(Errors.MISSING_PARAMS.value)
        return to_response_error(Errors.MISSING_PARAMS)
    try:
        context_query: ContextQuery = ContextQuery.parse_obj(context_query)
    except Exception as e:
        _logger.exception(e)
        return to_response_error(Errors.INVALID_QUERY_PARAMS)
    
    secrets = SSM().load_params(app_secrets_path)
    openai_api_key = secrets.get('openai_api_key', None)
    cohere_api_key = secrets.get('cohere_api_key', None)
    neo4j_user = secrets.get('neo4j_user', None)
    neo4j_password = secrets.get('neo4j_password', None)
    pinecone_api_key = secrets.get('pinecone_api_key', None)
    if not (openai_api_key and cohere_api_key and neo4j_user and neo4j_password and pinecone_api_key):
        _logger.exception(Errors.MISSING_SECRETS.value)
        return to_response_error(Errors.MISSING_SECRETS)
    pinecone = Pinecone(api_key=pinecone_api_key, environment='us-east1-gcp', index_name='beta', log_level=log_level)
    vectordb = VectorDB(db=pinecone)
    neo4j = Neo4j(uri=neo4j_uri, user=neo4j_user, password=neo4j_password, log_level=log_level)
    graphdb = GraphDB(db=neo4j)
    dstruct = DStruct(graphdb=graphdb, vectordb=vectordb, library=library, log_level=log_level)
    openai = OpenAI(api_key=openai_api_key, log_level=log_level)
    cohere = Cohere(api_key=cohere_api_key, log_level=log_level)
    reranker = Reranker(cohere=cohere, log_level=log_level)
    context_agent = ContextAgent(dstruct=dstruct, openai=openai, reranker=reranker, log_level=log_level)

    blocks: List[Block] = context_agent.fetch(Request(
        raw=context_query.lingua,
        token_limit=token_limit,
        next_token=next_token,
        end=BlockQuery(
            search_method=context_query.search_method,
            concepts=';'.join(context_query.concepts) if context_query.concepts else None,
            entities=context_query.entities,
            absolute_time_start=context_query.time_start,
            absolute_time_end=context_query.time_end,
            relative_time=context_query.time_sort,
            limit=context_query.limit,
            offset=context_query.offset,
            integrations=context_query.integrations,
        )
    ))
    _logger.debug(f'[main] blocks fetched: {str([block.id for block in blocks])}')
    response = { 'next_token': None }
    response_blocks: List[Dict] = []
    if blocks:
        for block in blocks:
            block_dict = {
                'id': block.id,
                'label': block.label,
                'integration': block.integration,
                'connection': block.connection,
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
    neo4j.close()
    return to_response_success(response)

