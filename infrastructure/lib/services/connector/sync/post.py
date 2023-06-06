import json
import os

import boto3

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

_batch = None

def handler(event: dict, context):
    global _batch

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
    if not (stage and user and connection and library):
        return {
            'statusCode': 400,
            'headers': HEADERS,
            'body': json.dumps({
                'error': 'missing params'
            })
        } 
    
    if not _batch:
        _batch = boto3.client('batch')
    
    response = _batch.submit_job(
        jobName=f'{stage}-{user}-{connection}-{library}-sync',
        jobQueue=job_queue,
        jobDefinition=job_definition,
        parameters={
            'connection': connection,
            'library': library,
        }
    )
    print(response)

    return {
        'statusCode': 200,
        'headers': HEADERS,
        'body': {
            'jobId': response.get('jobId', None) if response else None
        }
    }
