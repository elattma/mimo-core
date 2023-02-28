import json
import os
import time
from typing import List

import boto3
import ulid
from db.pc import KeyNamespaces, ParentChildDB, UserMessageItem
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.conversation.memory import \
    ConversationalBufferWindowMemory
from utils.responses import Errors, to_response_error, to_response_success

PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["history", "human_input"], 
    template="""Assistant is a large language model trained by OpenAI.

Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

{history}
Human: {human_input}
Assistant: """
)

secrets = None
llm_client = None
pc_db = None

def handler(event, context):
    global secrets
    global llm_client
    global pc_db

    stage = os.environ['STAGE']
    body = json.loads(event['body']) if event and event['body'] else None
    message = body['message'] if body else None
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not body or not message or not user or not stage:
        return to_response_error(Errors.MISSING_PARAMS)

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId="{stage}/Mimo/Integrations".format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    if llm_client is None:
        llm_client = OpenAI(temperature=0, openai_api_key=secrets['OPENAI_API_KEY'])

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
    chatgpt_chain = LLMChain(llm=llm_client, prompt=PROMPT_TEMPLATE, verbose=True, memory=memory)
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
