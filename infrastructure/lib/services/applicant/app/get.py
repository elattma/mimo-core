import os
from typing import List

from shared.model import Connection
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB, UserConnectionItem

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    app: str = path_parameters.get('app', None) if path_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    response_connections: List[Connection] = []
    if not app:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_namespace = KeyNamespaces.CONNECTION.value
        user_connection_items: List[UserConnectionItem] = _db.query(parent_key, child_namespace=child_namespace, Limit=100)
        response_connections = [user_connection_item.connection for user_connection_item in user_connection_items]
    else:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_key = '{namespace}{connection}'.format(namespace=KeyNamespaces.CONNECTION.value, connection=connection)
        try:
            user_connection_item: UserConnectionItem = _db.get(parent_key, child_key)
            response_connections = [user_connection_item.connection]
        except Exception as e:
            return to_response_error(Errors.DB_WRITE_FAILED)
    return to_response_success({
        'connections': [{
            'id': connection.id,
            'name': connection.name,
            'integration': connection.integration,
            'auth': {
                'type': connection.auth.type.value,
            },
            'created_at': connection.created_at,
            'ingested_at': connection.ingested_at
        } for connection in response_connections],
        'next_token': None
    })
