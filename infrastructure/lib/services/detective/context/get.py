import os

from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.context_basket.model import DataRequest
from mystery.data_agent import DataAgent
from util.response import Errors, to_response_error, to_response_success
from util.secrets import Secrets

secrets: Secrets = None
data_agent: DataAgent = None

def handler(event: dict, context):
    global secrets, data_agent

    stage: str = os.getenv('STAGE')
    graph_db_uri: str = os.getenv('GRAPH_DB_URI')
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None

    query: str = query_string_parameters.get('query', None) if query_string_parameters else None
    max_tokens: int = query_string_parameters.get('max_tokens', None) if query_string_parameters else None
    max_tokens = int(max_tokens) if max_tokens else 1600
    library: str = query_string_parameters.get('library', 'google-oauth2|108573573074253667565') if query_string_parameters else None

    if not (stage or graph_db_uri or query or max_tokens or library):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)
    if not data_agent:
        pinecone = Pinecone(
            api_key=secrets.get('PINECONE_API_KEY'), environment='us-east1-gcp'
        )
        neo4j = Neo4j(
            uri=graph_db_uri,
            user=secrets.get('GRAPH_DB_KEY'),
            password=secrets.get('GRAPH_DB_SECRET'),
        )
        openai = OpenAI(api_key=secrets.get('OPENAI_API_KEY'))
        data_agent = DataAgent(
            owner=library,
            vector_db=pinecone,
            graph_db=neo4j, 
            openai=openai, 
        )
    data_request = DataRequest(
        request=query,
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

