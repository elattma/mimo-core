import os

from aws.response import Errors, to_response_error, to_response_success
from aws.secrets import Secrets
from external.auth0_ import Auth0
from external.openai_ import OpenAI
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.context_basket.model import ContextBasket
from mystery.data_agent import DataAgent

secrets: Secrets = None
data_agent: DataAgent = None
auth0: Auth0 = None

def handler(event: dict, context):
    global secrets, data_agent, auth0

    mimo_test_token: str = os.environ['TEST_TOKEN']

    stage: str = os.environ['STAGE']
    graph_db_uri: str = os.environ['GRAPH_DB_URI']
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    question: str = query_string_parameters.get('question', None) if query_string_parameters else None
    max_tokens: int = query_string_parameters.get('max_tokens', None) if query_string_parameters else None
    max_tokens = int(max_tokens) if max_tokens else 1600
    test_token: str = query_string_parameters.get('test_token', None) if query_string_parameters else None
    user = 'google-oauth2|108573573074253667565'
    if not test_token or test_token != mimo_test_token:
        if not auth0:
            auth0 = Auth0(os.environ['STAGE'])
        user = auth0.validated_get_user(event.get('headers', {}).get('authorization', None))
        if not user:
            return to_response_error(Errors.INVALID_USER.value)

    if not (stage or graph_db_uri or question):
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
            owner=user,
            vector_db=pinecone,
            graph_db=neo4j, 
            openai=openai, 
        )
    context_basket: ContextBasket = data_agent.generate_context(question, max_tokens=max_tokens)
    answer = str(context_basket)
    
    return to_response_success({
        'answer': answer,
        'sources': [context.source for context in context_basket.contexts]
    })
