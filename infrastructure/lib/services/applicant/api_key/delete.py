import os

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    query_params: dict = event.get('queryStringParameters', None) if event else None
    id: str = query_params.get('id', None) if query_params else None
    app: str = query_params.get('app', None) if query_params else None

    if not (user and stage and id and app):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _db:
        _db = ParentChildDB(f'mimo-{stage}-pc')
    
    try:
        parent_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
        child_key = '{namespace}{api_key}'.format(namespace=KeyNamespaces.API_KEY.value, api_key=id)
        _db.delete(parent_key, child_key)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'success': True
    })
