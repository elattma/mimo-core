import os
from time import time
from typing import List

from shared.model import Library
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB, UserLibraryItem
from ulid import ulid

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    library: str = path_parameters.get('library', None) if path_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
    response_libraries: List[Library] = []
    if not library:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_namespace = KeyNamespaces.LIBRARY.value
        user_library_items: List[UserLibraryItem] = _db.query(parent_key, child_namespace=child_namespace, Limit=100)
        if user_library_items:
            response_libraries = [user_library_item.library for user_library_item in user_library_items]
        else:
            default_library = Library(id=ulid(), name='Default', created_at=int(time()))
            _db.write([UserLibraryItem(parent=parent_key, library=default_library)])
            response_libraries = [default_library]
    else:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
        try:
            user_library_item: UserLibraryItem = _db.get(parent_key, child_key)
            response_libraries = [user_library_item.library] if user_library_item else []
        except Exception as e:
            print(e)
            return to_response_error(Errors.DB_READ_FAILED)
    return to_response_success({
        'libraries': [{
            'id': library.id,
            'name': library.name,
            'created_at': library.created_at,
        } for library in response_libraries],
        'next_token': None
    })
