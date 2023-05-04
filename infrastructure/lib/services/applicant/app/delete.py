import os

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    app: str = path_parameters.get('app', None) if path_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage and app):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
    child_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    try:
        _db.delete(parent_key, child_key)
    except Exception as e:
        return to_response_error(Errors.DB_WRITE_FAILED)
    return to_response_success({
        'success': True,
    })
