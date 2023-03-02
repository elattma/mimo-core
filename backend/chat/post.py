import json
import os
import time
from typing import Generator, List

import boto3
import requests
import ulid
from data.docs import Docs
from data.fetcher import Fetcher
from db.pc import (KeyNamespaces, ParentChildDB, Roles, UserChatItem,
                   UserIntegrationItem)
from openai import ChatCompletion
from openai.openai_object import OpenAIObject
from utils.auth import refresh_token
from utils.responses import Errors, to_response_error, to_response_success

# TODO: update prompt or make easily configurable - use ssm?
MODEL = "gpt-3.5-turbo"

secrets = None
pc_db = None

def handler(event: dict, context):
    global secrets
    global pc_db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    stage: str = os.environ['STAGE']
    appsync_endpoint: str = os.environ['APPSYNC_ENDPOINT']

    headers: dict = event.get('headers', None) if event else None
    authorization: str = headers.get('Authorization', None) if headers else None

    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    chat: dict = body.get('chat', None) if body else None
    message_id: str = chat.get('id', None) if chat else None
    message: str = chat.get('message', None) if chat else None
    role: str = chat.get('role', None) if chat else None
    timestamp: int = chat.get('timestamp', None) if chat else None
    items: List[dict] = body.get('items', None) if body else None

    if not (user and stage and appsync_endpoint and authorization and message_id and message and role and timestamp):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId="{stage}/Mimo/Integrations".format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    openai_api_key = secrets['OPENAI_API_KEY'] if secrets and 'OPENAI_API_KEY' in secrets else None
    if not openai_api_key:
        return to_response_error(Errors.MISSING_SECRETS.value)

    # fetch conversational history and use as memory
    # TODO: experiment different strategies like spacy similarity, etc.
    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))
    chat_history: List[UserChatItem] = []
    try:
        chat_history = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.CHAT.value)
        chat_history.reverse()
    except Exception as e:
        print(e)
        print("empty history!")

    # TODO: fetch relevant context from selected items or knowledge base and use as context to prompt
    # TODO: hacky, move to other lambda/api under item. or somewhere else that's actually scalable enough to do this
    context_summary: List[str] = []
    if items is not None and len(items) > 0:
        # load auth
        user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
        for item in items:
            print(item)
            if not item or 'integration' not in item or not 'params' not in item:
                print('missing integration or params.. skipping!')
                continue
            
            integration_item = None
            for user_integration_item in user_integration_items:
                if user_integration_item.get_raw_child() == item['integration']:
                    integration_item = user_integration_item
                    break
            if not integration_item:
                print(f'no integration found for {item["integration"]}.. skipping!')
                continue

            integration = integration_item.get_raw_child()
            client_id = secrets.get(f'{integration}/CLIENT_ID')
            client_secret = secrets.get(f'{integration}/CLIENT_SECRET')
            if not client_id or not client_secret:
                print(f'missing secrets for {integration}.. skipping!')
                continue

            access_token = refresh_token(db=pc_db, client_id=client_id, client_secret=client_secret, item=item)
            if not access_token:
                print(f'failed to refresh token for {integration}.. skipping!')
                continue
                
            data_fetcher: Fetcher = None
            if item['integration'] == 'google':
                data_fetcher = Docs(access_token=access_token)
            if not data_fetcher:
                print(f'no data fetcher found for {integration}.. skipping!')
                continue

            for param in item['params']:
                print(param)
                if not param or 'id' not in param:
                    print('missing id.. skipping!')
                    continue

                data = data_fetcher.fetch(id=item['id'])
                print(data)
                if not data:
                    print(f'no data found for {integration}.. skipping!')
                    continue
            
                # TODO: summarize and add to prompt for now, refine method
                # chain = load_summarize_chain(llm=llm_client, chain_type="map_reduce")
                # summary = chain.run([Document(page_content=chunk.content) for chunk in data.chunks])
                # print(summary)
                # if summary:
                #     context_summary.append(summary)
            
    messages = [{ 'role': 'system', 'content': 'You are a helpful assistant.' }] \
        + [{ 'role': chat_item.role, 'content': chat_item.message } for chat_item in chat_history] \
            + [{ 'role': role, 'content': message }]
    print(messages)
    response_stream: Generator[OpenAIObject] = ChatCompletion.create(
        api_key=openai_api_key,
        model=MODEL,
        messages=messages,
        temperature=0,
        stream=True
    )
    print(response_stream)

    output_message_id = ulid.new().str
    output_role = Roles.ASSISTANT.value
    output_timestamp = int(time.time())

    output: str = ""
    accumulated_tokens: int = 0
    for response in response_stream:
        print(response)
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
                input_chat_id=message_id, 
                output_chat_id=output_message_id, 
                message=output, 
                role=Roles.ASSISTANT.value, 
                timestamp=output_timestamp
            )
            accumulated_tokens = 0

    if not output:
        return to_response_error(Errors.OPENAI_ERROR.value)
    print(output)

    parent = f'{KeyNamespaces.USER.value}{user}'
    input_message = UserChatItem(
        parent=parent, 
        child=f'{KeyNamespaces.CHAT.value}{message_id}', 
        message=message, 
        author=user, 
        role=Roles.USER.value, 
        timestamp=timestamp
    )
    output_message = UserChatItem(
        parent=parent, 
        child=f'{KeyNamespaces.CHAT.value}{output_message_id}', 
        message=output, 
        author=MODEL,
        role=output_role,
        timestamp=output_timestamp
    )
    pc_db.write([input_message, output_message])

    return to_response_success({
        'id': output_message_id,
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