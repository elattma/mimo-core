import os

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client._auth0 import Auth0
from app.client._neo4j import Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone
from app.client._secrets import Secrets
from app.mystery.qa_agent import Answer, QuestionAnswerAgent

secrets: Secrets = None
qa_agent: QuestionAnswerAgent = None
auth0: Auth0 = None

def handler(event: dict, context):
    global secrets, qa_agent, auth0

    if not auth0:
        auth0 = Auth0(os.environ["STAGE"])
    user = auth0.validated_get_user(event.get('headers', {}).get('authorization', None))
    if not user:
        return to_response_error(Errors.INVALID_USER.value)

    stage: str = os.environ["STAGE"]
    graph_db_uri: str = os.environ["GRAPH_DB_URI"]
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    question: str = query_string_parameters.get('question', None) if query_string_parameters else None

    if not (stage or graph_db_uri or question):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)
    if not qa_agent:
        pinecone = Pinecone(
            api_key=secrets.get("PINECONE_API_KEY"), environment="us-east1-gcp"
        )
        neo4j = Neo4j(
            uri=graph_db_uri,
            user=secrets.get("GRAPH_DB_KEY"),
            password=secrets.get("GRAPH_DB_SECRET"),
        )
        openai = OpenAI(api_key=secrets.get("OPENAI_API_KEY"))
        qa_agent = QuestionAnswerAgent(
            owner=user,
            vector_db=pinecone,
            graph_db=neo4j, 
            openai=openai, 
        )
    answer: Answer = qa_agent.debug_run(question)
    
    return to_response_success({
        'answer': answer.content,
        'sources': answer.sources
    })