import os
from typing import List

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB,
                                        UserChatItem)

db: ParentChildDB = None

def handler(event: dict, context):
    global db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    next_token: str = query_string_parameters.get('next_token', None) if query_string_parameters else None

    if not (user and stage):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not db:
        db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    query_args = {}
    if next_token:
        query_args['next_token'] = next_token
    user_chat_items: List[UserChatItem] = db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.CHAT.value, **query_args)

    return to_response_success([{
        'id': user_chat_item.get_raw_child(),
        'message': user_chat_item.message,
        'author': user_chat_item.author,
        'role': user_chat_item.role,
        'timestamp': user_chat_item.timestamp,
    } for user_chat_item in user_chat_items])