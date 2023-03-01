import os
from typing import List

from db.pc import KeyNamespaces, ParentChildDB, UserMessageItem
from utils.responses import Errors, to_response_error, to_response_success

pc_db = None

def handler(event, context):
    global pc_db

    user = event['requestContext']['authorizer']['principalId'] if event and 'requestContext' in event and 'authorizer' in event['requestContext'] and 'principalId' in event['requestContext']['authorizer'] else None
    stage = os.environ['STAGE']
    next_token = event['queryStringParameters']['next_token'] if event and 'queryStringParameters' in event and 'next_token' in event['queryStringParameters'] else None

    if not user or not stage:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    query_args = {}
    if next_token:
        query_args['next_token'] = next_token
    userMessageItems: List[UserMessageItem] = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.MESSAGE.value, **query_args)

    response = [userMessageItem.__dict__ for userMessageItem in userMessageItems]
    print(response)

    return to_response_success(response)