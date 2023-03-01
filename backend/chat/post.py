import json
import os
import time
from typing import Any, Dict, List, Union

import boto3
import requests
import ulid
from data.docs import Docs
from data.fetcher import Fetcher
from db.pc import (KeyNamespaces, ParentChildDB, UserIntegrationItem,
                   UserMessageItem)
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler, CallbackManager
from langchain.chains.conversation.memory import \
    ConversationalBufferWindowMemory
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.llms import OpenAI
from langchain.schema import AgentAction, AgentFinish, LLMResult
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
    appsync_endpoint = os.environ['APPSYNC_ENDPOINT']
    authorization = event['headers']['Authorization'] if event and 'headers' in event and 'Authorization' in event['headers'] else None
    body = json.loads(event['body']) if event and 'body' in event else None
    message = body['message'] if body and 'message' in body else None
    items = body['items'] if body and 'items' in body else None
    if not user or not stage or not appsync_endpoint or not authorization or not body or not message:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId="{stage}/Mimo/Integrations".format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    if llm_client is None:
        openai_api_key = secrets['OPENAI_API_KEY'] if secrets and 'OPENAI_API_KEY' in secrets else None
        if not openai_api_key:
            return to_response_error(Errors.MISSING_SECRETS.value)
        llm_client = OpenAI(
            streaming=True, 
            callback_manager=CallbackManager([StreamingWebsocketHandler(user_id=user, message_id=ulid.new().str, appsync_endpoint=appsync_endpoint, authorization=authorization)]), 
            verbose=True, 
            temperature=0,
            openai_api_key=openai_api_key
        )

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

class StreamingWebsocketHandler(BaseCallbackHandler):
    def __init__(self, user_id: str, message_id: str, appsync_endpoint: str, authorization: str):
        super().__init__()
        self.user_id = user_id
        self.message_id = message_id
        self.message = ''
        self.appsync_endpoint = appsync_endpoint
        self.authorization = authorization

    def send_message(self) -> None:
        if not self.message:
            return
        
        timestamp = int(time.time())
        query = 'mutation($userId: ID!, $messageId: ID!, $message: String!, $timestamp: Int!) { proxyMessage(userId: $userId, messageId: $messageId, message: $message, timestamp: $timestamp) { userId, messageId, message, timestamp }}'
        variables = json.dumps({
            "userId": self.user_id,
            "messageId": self.message_id,
            "message": self.message,
            "timestamp": timestamp
        })
        response = requests.post(
            self.appsync_endpoint, 
            headers={
                'Authorization': self.authorization.replace('Bearer ', '')
            },
            data=json.dumps({
                'query': query,
                'variables': variables
            })
        )
        appsync_response = response.json()

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        self.message += token
        if len(self.message) > 20:
            print(self.message)
            self.send_message()
            self.message = ''

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Run when LLM starts running."""

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Run when LLM ends running."""

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when LLM errors."""

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Run when chain starts running."""

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when chain errors."""

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Run when tool starts running."""

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> Any:
        """Run on agent action."""
        pass

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Run when tool ends running."""

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Run when tool errors."""

    def on_text(self, text: str, **kwargs: Any) -> None:
        """Run on arbitrary text."""

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Run on agent end."""