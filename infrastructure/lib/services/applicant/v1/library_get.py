import os
from typing import List

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, LibraryAppItem, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    app: str = query_string_parameters.get('app', None) if query_string_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage and app):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    app_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    items: List[LibraryAppItem] = []
    try:
        items = _db.child_query(app_key)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    return to_response_success({
        'libraries': [{
            'id': item.get_raw_parent(),
            'created_at': item.created_at,
        } for item in items]
    })
