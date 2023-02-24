import json
import os
import time

import boto3
import ulid
from db.pc import KeyNamespaces, ParentChildDB, UserMessageItem
from langchain import LLMChain, OpenAI, PromptTemplate
from langchain.chains.conversation.memory import \
    ConversationalBufferWindowMemory

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

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}

def handler(event, context):
    global secrets
    global llm_client
    global pc_db

    stage = os.environ['STAGE']
    body = json.loads(event['body']) if event and event['body'] else None
    message = body['message'] if body else None
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not body or not message or not user or not stage:
        return {
            "statusCode": 400,
            "headers": HEADERS,
        }

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId="{stage}/Mimo/Integrations".format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    if llm_client is None:
        llm_client = OpenAI(temperature=0, openai_api_key=secrets['OPENAI_API_KEY'])

    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    userMessageItems = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.MESSAGE.value)
    if not userMessageItems or len(userMessageItems) == 0:
        print("empty history!")
    chat_history = []
    for item in userMessageItems:
        if item['author'] == user:
            chat_history.append(message)

    memory = ConversationalBufferWindowMemory(k=3, buffer=chat_history)
    chatgpt_chain = LLMChain(llm=llm_client, prompt=PROMPT_TEMPLATE, verbose=True, memory=memory)
    output = chatgpt_chain.predict(human_input=message)

    timestamp = int(time.time())
    in_message = UserMessageItem(parent=user, child=ulid.new().str, author=user, message=message, timestamp=timestamp)
    out_message = UserMessageItem(parent=user, child=ulid.new().str, author="0.0.1", message=output, timestamp=timestamp)
    pc_db.write([in_message, out_message])

    return {
        "statusCode": 200,
        "headers": HEADERS,
        "body": json.dumps({
            "message": output
        })
    }