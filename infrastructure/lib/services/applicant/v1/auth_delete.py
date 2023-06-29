import os

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    query_parameters: dict = event.get('queryStringParameters', None) if event else None
    app: str = query_parameters.get('app', None) if query_parameters else None
    library: str = query_parameters.get('library', None) if query_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage and app and library):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    try:
        item = _db.get(f'{KeyNamespaces.USER.value}{user}', f'{KeyNamespaces.APP.value}{app}')
        if not item:
            return to_response_error(Errors.APP_NOT_FOUND)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)

    parent_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
    child_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    try:
        _db.delete(parent_key, child_key)
    except Exception as e:
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'success': True
    })
