import os
from typing import Dict

from auth.authorizer import Authorizer
from shared.model import AuthType, Integration, TokenAuth
from shared.response import Errors
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB
from state.params import SSM

_db: ParentChildDB = None
_integrations_dict: Dict[str, Integration] = None

def handler(event: dict, context):
    global _db, _integrations_dict

    stage: str = os.getenv('STAGE')
    integrations_path: str = os.getenv('INTEGRATIONS_PATH')
    user: str = event.get('user', None) if event else None
    library: str = event.get('library', None) if event else None
    connection: str = event.get('connection', None) if event else None

    if not (stage and integrations_path and user and library and connection):
        return {
            'error': Errors.MISSING_PARAMS.value
        }
    
    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
    parent = f'{KeyNamespaces.LIBRARY.value}{library}'
    child = f'{KeyNamespaces.CONNECTION.value}{connection}'
    item: LibraryConnectionItem = _db.get(parent, child)
    if not item:
        return {
            'error': Errors.INVALID_CONNECTION.value
        }
    
    integration_id = item.connection.integration
    if not _integrations_dict:
        _ssm = SSM()
        integration_params = _ssm.load_params(integrations_path)
        _integrations_dict = {}
        for id, integration_params in integration_params.items():
            _integrations_dict[id] = Integration.from_dict(integration_params)
    integration: Integration = _integrations_dict.get(integration_id) if _integrations_dict else None
    auth_type = item.connection.auth.type
    auth_params = None
    if auth_type in TokenAuth.get_possible_types():
        auth: TokenAuth = item.connection.auth
        if auth_type == AuthType.TOKEN_DIRECT:
            auth_params = {
                'access_token': auth.access_token,
            }
        elif auth_type == AuthType.TOKEN_OAUTH2:
            auth_strategy = integration.auth_strategies.get(AuthType.TOKEN_OAUTH2, None)
            refreshed = Authorizer.refresh_token_oauth2(auth_strategy, auth.refresh_token)
            auth_params = {
                'access_token': refreshed.access_token,
            }
        else:
            return {
                'error': Errors.INVALID_AUTH.value
            }
    else:
        return {
            'error': Errors.INVALID_AUTH.value
        }

    return {
        'params': {
            'user': user,
            'library': library,
            'connection': connection,
            'integration': integration_id,
            'last_ingested_at': item.connection.ingested_at,
            'airbyte_id': integration.airbyte_id,
            **auth_params,
        }
    }
