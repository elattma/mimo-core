import os
from typing import List

from boto3.dynamodb.conditions import Key
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

    try:
        item = _db.get(f'{KeyNamespaces.USER.value}{user}', f'{KeyNamespaces.APP.value}{app}')
        if not item:
            return to_response_error(Errors.APP_NOT_FOUND)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    
    library_namespace = KeyNamespaces.LIBRARY.value
    app_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    libraries = []
    try:
        app_libraries: List[LibraryAppItem] = _db.child_query(app_key, library_namespace)
        for app_library in app_libraries:
            libraries.append({
                'id': app_library.get_raw_parent(),
                'created_at': app_library.created_at,
            })
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    
    user_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
    try:
        response = _db.table.query(KeyConditionExpression=Key('parent').eq(user_key) & Key('child').begins_with(KeyNamespaces.LIBRARY.value))
        response_items = response.get('Items', None) if response else None
        if response_items:
            for response_item in response_items:
                item_child: str = response_item.get('child', None) if response_item else None
                if item_child and item_child.startswith(KeyNamespaces.LIBRARY.value):
                    library_id: str = item_child.replace(KeyNamespaces.LIBRARY.value, '')
                    created_at: int = response_item.get('created_at', None) if response_item else None
                    libraries.append({
                        'id': library_id,
                        'created_at': int(created_at) if created_at else 0,
                    })
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    return to_response_success({
        'libraries': libraries
    })
