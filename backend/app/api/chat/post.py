import json
import os
import time
from typing import List

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.api.util.stream import send_chat
from app.client._openai import OpenAI
from app.client._secrets import Secrets
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB, Roles,
                                        UserChatItem)
from ulid import ulid

MODEL = "gpt-3.5-turbo"

db: ParentChildDB = None
secrets: Secrets = None

def handler(event: dict, context):
    global db, secrets

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get(
        'authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    stage: str = os.environ['STAGE']
    appsync_endpoint: str = os.environ['APPSYNC_ENDPOINT']

    headers: dict = event.get('headers', None) if event else None
    authorization: str = headers.get(
        'Authorization', None) if headers else None

    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    chat: dict = body.get('chat', None) if body else None
    chat_id: str = chat.get('id', None) if chat else None
    message: str = chat.get('message', None) if chat else None
    role: str = chat.get('role', None) if chat else None
    timestamp: int = chat.get('timestamp', None) if chat else None
    items: List[dict] = body.get('items', None) if body else None

    if not (user and stage and appsync_endpoint and authorization and chat_id and message and role and timestamp):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)
    if not db:
        db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    openai_api_key = secrets.get('OPENAI_API_KEY', None) if secrets else None
    if not openai_api_key:
        return to_response_error(Errors.MISSING_SECRETS.value)

    # TODO: experiment different strategies like spacy similarity, etc.
    chat_history: List[UserChatItem] = []
    try:
        chat_history = db.query("{namespace}{user}".format(
            namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.CHAT.value)
    except Exception as e:
        print(e)
        print("empty history!")

    # TODO: fetch relevant context from selected items or knowledge base and use as context to prompt

    openai = OpenAI(api_key=openai_api_key)
    response_stream = openai.stream_chat_completion([])
    output_chat_id = ulid()
    output_role = Roles.ASSISTANT.value
    output_timestamp = int(time.time())
    
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

    if not output:
        return to_response_error(Errors.OPENAI_ERROR.value)

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
        message=output,
        author=MODEL,
        role=output_role,
        timestamp=output_timestamp
    )
    db.write([input_chat, output_chat])

    return to_response_success({
        'id': output_chat_id,
        'message': output,
        'author': MODEL,
        'role': output_role,
        'timestamp': output_timestamp
    })
