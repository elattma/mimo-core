import json
import os
from time import time
from typing import List

from shared.model import App
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentAppItem, ParentChildDB
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

    if not (user and stage and name):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    apps: List[ParentAppItem] = []
    parent = f'{KeyNamespaces.USER.value}{user}'
    child_namespace = KeyNamespaces.APP.value
    try:
        apps = _db.query(parent, child_namespace=child_namespace, Limit=100)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    if len(apps) >= 10:
        return to_response_error(Errors.APP_LIMIT_REACHED)
    elif len(apps) < 1:
        return to_response_error(Errors.APP_LIMIT_REACHED)

    now_timestamp: int = int(time())
    app_id = ulid()
    app = App(id=app_id, name=name, created_at=now_timestamp)
    user_app_item = ParentAppItem(parent, app)
    try:
        _db.write([user_app_item])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'app': {
            'id': app.id,
            'name': app.name,
            'created_at': app.created_at
        }
    })
