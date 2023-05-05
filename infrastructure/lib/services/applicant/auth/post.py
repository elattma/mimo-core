import json
import os

from helper.kms import KMS
from shared.model import App
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentAppItem, ParentChildDB

_db: ParentChildDB = None
_kms: KMS = None

def handler(event: dict, context):
    global _db, _kms

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    token: str = body.get('token', None) if body else None
    kms_key_id: str = os.getenv('KMS_KEY_ID')
    auth_endpoint: str = os.getenv('AUTH_ENDPOINT')
    stage: str = os.getenv('STAGE')

    if not (user and stage and kms_key_id and auth_endpoint and token):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    child_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    response_app: App = None
    try:
        user_app_item: ParentAppItem = _db.get(parent_key, child_key)
        response_app: App = user_app_item.app
    except Exception as e:
        return to_response_error(Errors.DB_READ_FAILED)
    
    if not response_app:
        return to_response_error(Errors.APP_NOT_FOUND)

    if not _kms:
        _kms = KMS()
    
    token = _kms.sign({
        'app': {
            'id': response_app.id,
            'name': response_app.name
        },
        'user': user
    }, key_id=kms_key_id)
    return to_response_success({
        'authLink': '{auth_endpoint}?token={token}'.format(auth_endpoint=auth_endpoint, token=token)
    })
