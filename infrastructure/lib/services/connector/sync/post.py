import json
import os
from typing import Dict

from shared.model import SyncStatus
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    connection: str = body.get('connection', None) if body else None

    if not (user and stage and connection):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
    parent = f'{KeyNamespaces.USER.value}{user}'
    child = f'{KeyNamespaces.CONNECTION.value}{connection}'
    condition_expression = 'attribute_exists(parent) AND attribute_exists(child)'
    attributes: Dict = _db.update(parent, child, { 'sync_status': SyncStatus.IN_PROGRESS.value }, ReturnValues='ALL_OLD', ConditionExpression=condition_expression)
    if attributes and attributes.get('sync_status', None) == SyncStatus.IN_PROGRESS.value:
        return to_response_error(Errors.SYNC_IN_PROGRESS)
    
    # call coalescer
    
    return to_response_success({
        'success': True
    })
