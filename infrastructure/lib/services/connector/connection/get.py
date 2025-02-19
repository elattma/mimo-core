import os
from time import time
from typing import List

from shared.model import Connection, Library
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import (KeyNamespaces, LibraryConnectionItem, ParentChildDB,
                          UserLibraryItem)
from ulid import ulid

_db: ParentChildDB = None


def handler(event: dict, context):
    global _db

    stage = os.getenv('STAGE')
    if not (stage):
        raise Exception('missing env vars!')

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    connection: str = path_parameters.get('connection', None) if path_parameters else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    library: str = query_string_parameters.get('library', None) if query_string_parameters else None

    if not user:
        return to_response_error(Errors.MISSING_PARAMS)

    if connection and not library:
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    if not library:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_namespace = KeyNamespaces.LIBRARY.value
        user_library_items: List[UserLibraryItem] = _db.query(parent_key, child_namespace=child_namespace, Limit=100)
        if not user_library_items:
            default_library = Library(id=ulid(), name='Default', created_at=int(time()))
            try:
                _db.write([UserLibraryItem(parent=parent_key, library=default_library)])
            except Exception as e:
                print(f'error writing default library: {e}')
                return to_response_error(Errors.DB_WRITE_FAILED)
            library = default_library.id
        else:
            library = user_library_items[0].library.id
    
    response_connections: List[Connection] = []
    if not connection:
        parent_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
        child_namespace = KeyNamespaces.CONNECTION.value
        user_connection_items: List[LibraryConnectionItem] = _db.query(parent_key, child_namespace=child_namespace, Limit=100)
        response_connections = [user_connection_item.connection for user_connection_item in user_connection_items]
    else:
        parent_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
        child_key = '{namespace}{connection}'.format(namespace=KeyNamespaces.CONNECTION.value, connection=connection)
        try:
            user_connection_item: LibraryConnectionItem = _db.get(parent_key, child_key)
            response_connections = [user_connection_item.connection]
        except Exception as e:
            return to_response_error(Errors.DB_READ_FAILED)
    
    if response_connections:
        response_connections.sort(key=lambda connection: connection.created_at, reverse=True)

    return to_response_success({
        'library': library,
        'connections': [{
            'id': connection.id,
            'name': connection.name,
            'integration': connection.integration,
            'auth': connection.auth.as_dict() if connection.auth else None,
            'config': connection.config,
            'created_at': connection.created_at,
            'sync': connection.sync.as_dict() if connection.sync else None
        } for connection in response_connections],
        'next_token': None
    })
