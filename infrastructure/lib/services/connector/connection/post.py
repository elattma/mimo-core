import json
import os
from time import time
from typing import Dict

from auth.base import AuthStrategy
from shared.model import Auth, AuthType, Connection, Integration
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB
from state.params import SSM
from ulid import ulid

_db: ParentChildDB = None
_integrations_dict: Dict[str, Integration] = None

def handler(event: dict, context):
    global _db, _integrations_dict

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    integrations_path: str = os.getenv('INTEGRATIONS_PATH')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    library: str = body.get('library', None) if body else None
    integration_id: str = body.get('integration', None) if body else None
    name: str = body.get('name', None) if body else None
    auth_strategy: Dict = body.get('auth_strategy', None) if body else None
    type: str = auth_strategy.get('type', None) if auth_strategy else None
    type: AuthType = AuthType(type) if type else None

    if not (user and stage and library and name and integration_id and type):
        return to_response_error(Errors.MISSING_PARAMS.value)

    now_timestamp: int = int(time())
    if not _integrations_dict:
        _ssm = SSM()
        integration_params = _ssm.load_params(integrations_path)
        _integrations_dict = {}
        for id, integration_params in integration_params.items():
            _integrations_dict[id] = Integration.from_dict(integration_params)
    integration: Integration = _integrations_dict.get(integration_id) if _integrations_dict else None
    strategy: AuthStrategy = integration.auth_strategies.get(type, None)
    if not (integration and strategy):
        return to_response_error(Errors.INVALID_AUTH.value)
    
    auth_strategy.pop('type', None)
    auth: Auth = strategy.auth(**auth_strategy, grant_type='authorization_code')
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
    parent = f'{KeyNamespaces.LIBRARY.value}{library}'
    try:
        _db.write([LibraryConnectionItem(parent, connection)])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'connection': {
            'id': connection.id,
            'name': connection.name,
            'integration': connection.integration,
            'auth': connection.auth.as_dict() if connection.auth else None,
            'created_at': connection.created_at
        }
    })
