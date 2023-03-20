import json
import os
import time
from typing import Generator, List

import requests
from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client._secrets import Secrets
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB, Roles,
                                        UserChatItem)
from openai import ChatCompletion
from openai.openai_object import OpenAIObject
from ulid import ulid

MODEL = "gpt-3.5-turbo"

db: ParentChildDB = None
secrets: Secrets = None

def handler(event: dict, context):
    global secrets

    request_context: dict = event.get(
        'requestContext', None) if event else None
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
    summary: str = None

    messages = [{ 'role': 'system', 'content': 'You are a helpful assistant.' }]
    if summary:
        messages.append({ 'role': 'user', 'content': summary })
    messages.extend([{ 'role': chat_item.role, 'content': chat_item.message } for chat_item in chat_history])
    messages.append({ 'role': role, 'content': message })
    print(messages)

    response_stream: Generator[OpenAIObject] = ChatCompletion.create(
        api_key=openai_api_key,
        model=MODEL,
        messages=messages,
        temperature=0,
        stream=True
    )
    output_chat_id = ulid()
    output_role = Roles.ASSISTANT.value
    output_timestamp = int(time.time())

    output: str = ""
    accumulated_tokens: int = 0
    for response in response_stream:
        choices: List[dict] = response.get('choices', None) if response else None
        if not choices or len(choices) == 0:
            continue

        for choice in choices:
            delta: dict = choice.get('delta', None) if choice else None
            streamed_output: dict = delta.get('content', None) if delta else None
            if not streamed_output:
                continue
            output += streamed_output
            accumulated_tokens += len(streamed_output)
        if accumulated_tokens > 20:
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
            accumulated_tokens = 0

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


def send_chat(appsync_endpoint: str, authorization: str, user_id: str, input_chat_id: str, output_chat_id: str, message: str, role: str, timestamp: int) -> None:
    if not message:
        return

    query = 'mutation($input: ChatInput!) { proxyChat(input: $input) { userId, inputChatId, outputChatId, message, role, timestamp }}'
    variables = json.dumps({
        "input": {
            "userId": user_id,
            "inputChatId": input_chat_id,
            "outputChatId": output_chat_id,
            "message": message,
            "role": role,
            "timestamp": timestamp
        }
    })
    response = requests.post(
        appsync_endpoint,
        headers={
            'Authorization': authorization.replace('Bearer ', '')
        },
        data=json.dumps({
            'query': query,
            'variables': variables
        })
    )
    appsync_response = response.json()
    print(appsync_response)
