import json
import os

from db.pc import KeyNamespaces, ParentChildDB

pc_db = None

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}

def handler(event, context):
    global pc_db

    stage = os.environ['STAGE']
    next_token = event['queryStringParameters']['next_token'] if event and event['queryStringParameters'] else None
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not user or not stage:
        return {
            "statusCode": 400,
            "headers": HEADERS,
        }

    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    query_args = {}
    if next_token:
        query_args['next_token'] = next_token
    userMessageItems = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.MESSAGE.value, **query_args)

    response = [userMessageItem.to_dict() for userMessageItem in userMessageItems]
    print(response)

    return {
        "statusCode": 200,
        "headers": HEADERS,
        "body": json.dumps(response)
    }