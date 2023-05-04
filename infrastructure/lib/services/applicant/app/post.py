import json
import os
from time import time
from typing import Dict

from auth.authorizer import Authorizer
from shared.model import Auth, AuthType, Connection, Integration, TokenAuth
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB, UserConnectionItem
from state.params import SSM
from ulid import ulid

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    name: str = body.get('name', None) if body else None
    auth_strategy: Dict = body.get('auth_strategy', None) if body else None
    type: str = auth_strategy.get('type', None) if auth_strategy else None

    if not (user and stage and name and integration_id and type):
        return to_response_error(Errors.MISSING_PARAMS.value)

    now_timestamp: int = int(time())
    auth: Auth = None    
    if not auth:
        return to_response_error(Errors.AUTH_FAILED)
    
    connection = Connection(
        id=ulid(),
        name=name,
        integration=integration.id,
        auth=auth,
        created_at=now_timestamp
    )

    if not _db: 
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    parent = f'{KeyNamespaces.USER.value}{user}'
    try:
        _db.write([UserConnectionItem(parent, connection)])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'connection': {
            'id': connection.id,
            'name': connection.name,
            'integration': connection.integration,
            'auth': {
                'type': connection.auth.type.value,
            },
            'created_at': connection.created_at,
            'ingested_at': connection.ingested_at
        }
    })
