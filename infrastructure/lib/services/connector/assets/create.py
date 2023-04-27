import json
import os
from time import time
from typing import Dict

from ulid import ulid
from util.authorizer import Authorizer, TokenOAuth2Params
from util.dynamo import KeyNamespaces, ParentChildDB, UserConnectionItem
from util.model import Auth, Connection, Integration
from util.params import SSM
from util.response import Errors, to_response_error, to_response_success
from util.secrets import Secrets

_db: ParentChildDB = None
_secrets: Secrets = None
_integrations_dict: Dict[str, Integration] = None

def handler(event: dict, context):
    global _db, _secrets, _integrations_dict

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    integrations_path: str = os.getenv('INTEGRATIONS_PATH')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    name: str = body.get('name', None) if body else None
    integration_id: str = body.get('integration', None) if body else None
    token_oauth2: str = body.get('token_oauth2', None) if body else None
    token_oauth2: dict = json.loads(token_oauth2) if token_oauth2 else None

    if not (user and stage and name and integration_id and token_oauth2):
        return to_response_error(Errors.MISSING_PARAMS.value)
    
    auth: Auth = None
    if token_oauth2:
        if not _secrets:
            _secrets = Secrets(stage)
        if not _integrations_dict:
            _ssm = SSM()
            nested_params = _ssm.load_nested_params(integrations_path)
            _integrations_dict = {}
            for id, integration_params in nested_params.items():
                _integrations_dict[id] = Integration(**integration_params)
        integration: Integration = _integrations_dict.get(integration_id) if _integrations_dict else None
        client_id = _secrets.get(f'{id}/CLIENT_ID')
        client_secret = _secrets.get(f'{id}/CLIENT_SECRET')
        code = token_oauth2.get('code', None) if token_oauth2 else None
        redirect_uri = token_oauth2.get('redirect_uri', None) if token_oauth2 else None
        print(id)
        print(_integrations_dict)
        print(integration)
        print(client_id)
        print(client_secret)
        print(code)
        print(redirect_uri)
        if not (integration and client_id and client_secret and code and redirect_uri):
            return to_response_error(Errors.INVALID_AUTH)
        params: TokenOAuth2Params = TokenOAuth2Params(
            authorize_endpoint=integration.authorize_endpoint,
            client_id=client_id,
            client_secret=client_secret,
            code=code,
            redirect_uri=redirect_uri,
        )
        auth = Authorizer.token_oauth2(params)

    if not auth:
        return to_response_error(Errors.AUTH_FAILED)

    connection = Connection(
        id=ulid(),
        name=name,
        integration=integration,
        auth=auth,
        created_at=int(time())
    )

    if not db: 
        db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    parent = f'{KeyNamespaces.USER.value}{user}'
    try:
        db.write([UserConnectionItem(parent, connection)])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED.value)

    return to_response_success({
        'connection': connection.to_response()
    })
