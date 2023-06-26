import json
import os
from time import time
from typing import Dict

import boto3
from shared.response import Errors, to_response_error, to_response_success


def handler(event: dict, context):
    stage = os.getenv('STAGE')
    sfn_arn = os.getenv('SFN_ARN')
    if not (stage and sfn_arn):
        raise Exception('missing env vars!')

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    body: str = event.get('body', None) if event else None
    body: Dict = json.loads(body) if body else None
    connection: str = body.get('connection', None) if body else None
    integration: str = body.get('integration', None) if body else None
    library: str = body.get('library', None) if body else None

    if not (user and connection and integration and library):
        return to_response_error(Errors.MISSING_PARAMS)

    step_functions = boto3.client('stepfunctions')
    response = step_functions.start_execution(
        stateMachineArn=sfn_arn,
        input=json.dumps({
            'input': {
                'connection': connection,
                'library': library,
                'integration': integration
            },
            'timestamp': str(int(time()))
        })
    )
    print(response)
    if response.get('ResponseMetadata', {}).get('HTTPStatusCode', None) != 200:
        return to_response_error(Errors.SFN_FAILED)

    return to_response_success({
        'success': True,
    })