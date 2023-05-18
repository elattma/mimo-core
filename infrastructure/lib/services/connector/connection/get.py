import os
from typing import List

from shared.model import Connection
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    connection: str = path_parameters.get('connection', None) if path_parameters else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    library: str = query_string_parameters.get('library', None) if query_string_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage and library):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
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
    return to_response_success({
        'connections': [{
            'id': connection.id,
            'name': connection.name,
            'integration': connection.integration,
            'auth': {
                'type': connection.auth.type.value,
            },
            'created_at': connection.created_at,
            'ingested_at': connection.ingested_at,
            'sync_status': connection.sync_status.value if connection.sync_status else None,
        } for connection in response_connections],
        'next_token': None
    })
