import os
from typing import List

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import (KeyNamespaces, LibraryAppItem, ParentChildDB,
                          ParentChildItem)

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
        user_libraries: List[ParentChildItem] = _db.query(user_key, library_namespace)
        for user_library in user_libraries:
            libraries.append({
                'id': user_library.get_raw_parent(),
                'created_at': 0,
            })
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    return to_response_success({
        'libraries': libraries
    })
