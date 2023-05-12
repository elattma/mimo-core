import os
from typing import List

from shared.model import ApiKey, App
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import (AppApiKeyItem, KeyNamespaces, ParentAppItem,
                          ParentChildDB)

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    app: str = path_parameters.get('app', None) if path_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    response_apps: List[App] = []
    response_api_keys: List[ApiKey] = []
    if not app:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_namespace = KeyNamespaces.APP.value
        user_app_items: List[ParentAppItem] = _db.query(parent_key, child_namespace=child_namespace, Limit=100)
        response_apps = [user_app_item.app for user_app_item in user_app_items]
    else:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
        child_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
        try:
            user_app_item: ParentAppItem = _db.get(parent_key, child_key)
            response_apps = [user_app_item.app]
            response_api_keys = get_api_keys(app)
        except Exception as e:
            print(e)
            return to_response_error(Errors.DB_READ_FAILED)
    return to_response_success({
        'apps': [{
            'id': app.id,
            'name': app.name,
            'created_at': app.created_at,
        } for app in response_apps],
        'api_keys': [{
            'id': api_key.id,
            'name': api_key.name,
            'app': api_key.app,
            'created_at': api_key.created_at,
        } for api_key in response_api_keys],
        'next_token': None
    })

def get_api_keys(app: str) -> List[ApiKey]:
    parent_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=app)
    child_namespace = KeyNamespaces.API_KEY.value
    items: List[AppApiKeyItem] = _db.query(parent_key, child_namespace, Limit=100)
    api_keys: List[ApiKey] = [item.api_key for item in items]
    return api_keys
