import json
import os
from time import time
from uuid import uuid4

from shared.model import ApiKey
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import AppApiKeyItem, KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    app: str = body.get('app', None) if body else None
    name: str = body.get('name', None) if body else None

    if not (user and stage and app and name):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _db:
        _db = ParentChildDB(stage)
    
    api_key = ApiKey(
        id=str(uuid4()),
        name=name,
        app=app,
        owner=user,
        created_at=int(time())
    )
    try:
        item = AppApiKeyItem(
            parent='{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app),
            api_key=api_key
        )
        _db.write([item])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'apiKey': api_key.__dict__
    })
