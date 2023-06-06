import json
import os

import boto3
from shared.response import Errors, to_response_error, to_response_success
from shared.sync_state import SyncState
from state.dynamo import ParentChildDB

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

_batch = None
_sync_state: SyncState = None

def handler(event: dict, context):
    global _batch, _sync_state

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    stage: str = os.getenv('STAGE')
    job_queue: str = os.getenv('JOB_QUEUE')
    job_definition: str = os.getenv('JOB_DEFINITION')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    connection: str = body.get('connection', None) if body else None
    library: str = body.get('library', None) if body else None
    if not (stage and job_queue and job_definition and user and connection and library):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _batch:
        _batch = boto3.client('batch')
    if not _sync_state:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
        _sync_state = SyncState(_db, library_id=library, connection_id=connection)

    if _sync_state.is_locked():
        return to_response_error(Errors.SYNC_IN_PROGRESS)

    _sync_state.hold_lock()
    response = _batch.submit_job(
        jobName=f'{stage}-{connection}-{library}-sync',
        jobQueue=job_queue,
        jobDefinition=job_definition,
        parameters={
            'connection': connection,
            'library': library,
        }
    )
    print(response)
    if not (response and response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0) == 200):
        _sync_state.release_lock(False)
        return to_response_error(Errors.BATCH_SUBMIT_FAILED)

    return to_response_success({
        'success': True,
    })
