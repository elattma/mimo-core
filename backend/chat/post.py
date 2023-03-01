import json
import os
import time
from typing import List

import boto3
import ulid
from data.docs import Docs
from data.fetcher import Fetcher
from db.pc import (KeyNamespaces, ParentChildDB, UserIntegrationItem,
                   UserMessageItem)
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.conversation.memory import \
    ConversationalBufferWindowMemory
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from utils.auth import refresh_token
from utils.responses import Errors, to_response_error, to_response_success

# TODO: update prompt or make easily configurable - use ssm?
TEMPLATE = """Assistant is a large language model trained by OpenAI.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

{{history}}
Human: {{human_input}}
Context: {context_summary}
Assistant: """

secrets = None
llm_client = None
pc_db = None

def handler(event, context):
    global secrets
    global llm_client
    global pc_db

    user = event['requestContext']['authorizer']['principalId'] if event and 'requestContext' in event and 'authorizer' in event['requestContext'] and 'principalId' in event['requestContext']['authorizer'] else None
    stage = os.environ['STAGE']
    body = json.loads(event['body']) if event and 'body' in event else None
    message = body['message'] if body and 'message' in body else None
    items = body['items'] if body and 'items' in body else None
    if not user or not stage or not body or not message:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId="{stage}/Mimo/Integrations".format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    if llm_client is None:
        openai_api_key = secrets['OPENAI_API_KEY'] if secrets and 'OPENAI_API_KEY' in secrets else None
        if not openai_api_key:
            return to_response_error(Errors.MISSING_SECRETS.value)
        llm_client = OpenAI(temperature=0, openai_api_key=openai_api_key)

    # fetch conversational history and use as memory
    # TODO: experiment different strategies like spacy similarity, etc.
    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))
    chat_history = []
    try:
        userMessageItems: List[UserMessageItem] = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.MESSAGE.value)
        for item in userMessageItems:
            if item and item.author == user:
                chat_history.append(item.message)
    except Exception as e:
        print(e)
        print("empty history!")
    memory = ConversationalBufferWindowMemory(k=3, buffer=chat_history[0:3])

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
                chain = load_summarize_chain(llm=llm_client, chain_type="map_reduce")
                summary = chain.run([Document(page_content=chunk.content) for chunk in data.chunks])
                print(summary)
                if summary:
                    context_summary.append(summary)
            
    template = TEMPLATE.format(context_summary='; '.join(context_summary))
    print(template)
    prompt_template = PromptTemplate(
        input_variables=["history", "human_input"], 
        template=template
    )
    chatgpt_chain = LLMChain(llm=llm_client, prompt=prompt_template, verbose=True, memory=memory)
    output = chatgpt_chain.predict(human_input=message)

    parent = f'{KeyNamespaces.USER.value}{user}'
    in_child = f'{KeyNamespaces.MESSAGE.value}{ulid.new().str}'
    out_child = f'{KeyNamespaces.MESSAGE.value}{ulid.new().str}'
    timestamp = int(time.time())
    in_message = UserMessageItem(parent=parent, child=in_child, author=user, message=message, timestamp=timestamp)
    out_message = UserMessageItem(parent=parent, child=out_child, author="0.0.1", message=output, timestamp=timestamp)
    pc_db.write([in_message, out_message])

    return to_response_success({
        "message": output
    })
