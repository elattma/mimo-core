import json
import os
import time
from typing import List

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.api.util.stream import send_chat
from app.client._neo4j import Neo4j
from app.client._openai import OpenAI
from app.client._pinecone import Pinecone
from app.client._secrets import Secrets
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB, Roles,
                                        UserChatItem)
from app.mystery.system import ChatSystem
from ulid import ulid

MODEL = "gpt-3.5-turbo"

db: ParentChildDB = None
secrets: Secrets = None
system: ChatSystem = None

def handler(event: dict, context):
    global db, secrets, system

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get(
        'authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    stage: str = os.environ['STAGE']
    appsync_endpoint: str = os.environ['APPSYNC_ENDPOINT']
    graph_db_uri: str = os.environ['GRAPH_DB_URI']

    headers: dict = event.get('headers', None) if event else None
    authorization: str = headers.get('Authorization', None) if headers else None

    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    chat: dict = body.get('chat', None) if body else None
    chat_id: str = chat.get('id', None) if chat else None
    message: str = chat.get('message', None) if chat else None
    timestamp: int = chat.get('timestamp', None) if chat else None
    contextualized: bool = body.get('contextualized', None) if chat else None
    items: List[dict] = body.get('items', None) if body else None

    if not (user and stage and appsync_endpoint and authorization and chat_id and message and timestamp):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)
    if not db:
        db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    openai_api_key = secrets.get('OPENAI_API_KEY')
    if not openai_api_key:
        return to_response_error(Errors.MISSING_SECRETS.value)

    chat_history: List[UserChatItem] = []
    try:
        chat_history = db.query("{namespace}{user}".format(
            namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.CHAT.value)
    except Exception as e:
        print(e)
        print("empty history!")

    # TODO: fetch relevant context from selected items or knowledge base and use as context to prompt

    if not system:
        openai = OpenAI(api_key=openai_api_key)
        graph_db = Neo4j(
            uri=graph_db_uri,
            user=secrets.get("GRAPH_DB_KEY"),
            password=secrets.get("GRAPH_DB_SECRET")
        )
        vector_db = Pinecone(api_key=secrets.get("PINECONE_API_KEY"), environment="us-east1-gcp", index_name='beta')
        system = ChatSystem(user, graph_db, vector_db, openai)

    output_chat_id = ulid()
    output_role = Roles.ASSISTANT.value
    output_timestamp = int(time.time())

    response_stream = system.stream_run(message)
    final_response: str = ''
    for output in response_stream:
        send_chat(
            appsync_endpoint=appsync_endpoint, 
            authorization=authorization, 
            user_id=user, 
            input_chat_id=chat_id, 
            output_chat_id=output_chat_id, 
            message=output, 
            role=Roles.ASSISTANT.value, 
            timestamp=output_timestamp
        )
        final_response = output

    parent = f'{KeyNamespaces.USER.value}{user}'
    input_chat = UserChatItem(
        parent=parent,
        child=f'{KeyNamespaces.CHAT.value}{chat_id}',
        message=message,
        author=user,
        role=Roles.USER.value,
        timestamp=timestamp
    )
    output_chat = UserChatItem(
        parent=parent,
        child=f'{KeyNamespaces.CHAT.value}{output_chat_id}',
        message=final_response,
        author=MODEL,
        role=output_role,
        timestamp=output_timestamp
    )
    db.write([input_chat, output_chat])

    return to_response_success({
        'id': output_chat_id,
        'message': final_response,
        'author': MODEL,
        'role': output_role,
        'timestamp': str(output_timestamp)
    })