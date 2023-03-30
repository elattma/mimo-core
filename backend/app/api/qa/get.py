import os

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client._neo4j import Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone
from app.client._secrets import Secrets
from app.mystery.qa_agent import Answer, QuestionAnswerAgent

secrets: Secrets = None
qa_agent: QuestionAnswerAgent = None


def handler(event: dict, context):
    global secrets, qa_agent

    request_context: dict = event.get("requestContext", None) if event else None
    authorizer: dict = (
        request_context.get("authorizer", None) if request_context else None
    )
    user: str = authorizer.get("principalId", None) if authorizer else None

    stage: str = os.environ["STAGE"]
    graph_db_uri: str = os.environ["GRAPH_DB_URI"]

    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    question: str = query_string_parameters.get('question', None) if query_string_parameters else None

    if not (user and stage):
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
    answer: Answer = qa_agent.run(question, ['email', 'crm', 'documents', 'customer_support'])
    
    return to_response_success({
        'answer': answer.content,
        'sources': answer.sources
    })