import json
import os
import time
from typing import Generator, List

import requests
from app.db.pc import (KeyNamespaces, ParentChildDB, Roles, UserChatItem,
                       UserIntegrationItem)
from app.fetcher.base import Fetcher
from app.util.response import Errors, to_response_error, to_response_success
from app.util.secret import Secret
from openai import ChatCompletion
from openai.openai_object import OpenAIObject
from ulid import ulid

# TODO: update prompt or make easily configurable - use ssm?
MODEL = "gpt-3.5-turbo"

def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    stage: str = os.environ['STAGE']
    appsync_endpoint: str = os.environ['APPSYNC_ENDPOINT']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']

    headers: dict = event.get('headers', None) if event else None
    authorization: str = headers.get('Authorization', None) if headers else None

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

    secrets = Secret(stage)
    openai_api_key = secrets.get('OPENAI_API_KEY') if secrets else None
    if not openai_api_key:
        return to_response_error(Errors.MISSING_SECRETS.value)

    # fetch conversational history and use as memory
    # TODO: experiment different strategies like spacy similarity, etc.
    db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))
    chat_history: List[UserChatItem] = []
    try:
        chat_history = db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.CHAT.value)
    except Exception as e:
        print(e)
        print("empty history!")

    # TODO: fetch relevant context from selected items or knowledge base and use as context to prompt
    # TODO: hacky, move to other lambda/api under item. or somewhere else that's actually scalable enough to do this
    context_summary: List[str] = []
    if items is not None and len(items) > 0:
        user_integration_items: List[UserIntegrationItem] = db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)

        for item in items:
            item_integration: str = item.get('integration', None) if item else None
            item_params: dict = item.get('params', None) if item else None
            if not (item_integration and item_params):
                print('missing integration or params.. skipping!')
                continue

            client_id = secrets.get(f'{item_integration}/CLIENT_ID')
            client_secret = secrets.get(f'{item_integration}/CLIENT_SECRET')

            fetcher: Fetcher = None

            # TODO: optimize
            if item_integration == 'upload':
                fetcher = Fetcher.create(item_integration, {
                    'bucket': upload_item_bucket,
                    'prefix': f'{user}/'
                })
            else: 
                for user_integration_item in user_integration_items:
                    if user_integration_item.get_raw_child() == item_integration:
                        fetcher = Fetcher.create(item_integration, {
                            'client_id': client_id,
                            'client_secret': client_secret,
                            'access_token': user_integration_item.access_token,
                            'refresh_token': user_integration_item.refresh_token,
                            'expiry_timestamp': user_integration_item.expiry_timestamp
                        })
                        break
            
            if not fetcher:
                print('no fetcher found.. skipping!')
                continue

            for param in item_params:
                if not (param or param.get('id', None)):
                    print('missing id.. skipping!')
                    continue
                
                data = fetcher.fetch(id=param['id'])
                if not data:
                    print(f'no data found for {item_integration}.. skipping!')
                    continue

                context_summary.extend([chunk.content for chunk in data.chunks])
                
    summary: str = ''
    if len(context_summary) > 0:
        while len(context_summary) > 1:
            slice_index = min(5, len(context_summary))
            messages = [{ 'role': 'system', 'content': 'You are an assistant who summarizes.' }]
            messages.extend([{ 'role': 'user', 'content': context } for context in context_summary[:slice_index]])
            messages.append({ 'role': 'user', 'content': 'Summarize the above context in a few sentences.'})
            response = ChatCompletion.create(
                api_key=openai_api_key,
                model=MODEL,
                messages=messages,
                temperature=0
            )
            choices = response.get('choices', None) if response else None
            choice = choices[0] if choices and len(choices) > 0 else None
            choice_message = choice.get('message', None) if choice else None
            content = choice_message.get('content', None) if choice_message else None
            if content:
                context_summary.append(content)
            context_summary = context_summary[slice_index:]
        summary = context_summary[0]

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