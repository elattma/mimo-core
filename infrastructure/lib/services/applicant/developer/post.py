import os
import re
from time import time
from uuid import uuid4

import boto3
from shared.response import Errors, to_response_error, to_response_success
from state.params import SSM

_db = None
_ssm = None
_apig = None

def handler(event: dict, context):
    global _db, _ssm, _apig
    waitlist_table: str = os.getenv('WAITLIST_TABLE')
    stage: str = os.getenv('STAGE')
    usage_plans_path: str = os.getenv('USAGE_PLANS_PATH')

    if not (waitlist_table and stage and usage_plans_path):
        return to_response_error(Errors.MISSING_ENV)

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None

    if not user:
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _db:
        _db = boto3.resource('dynamodb').Table(waitlist_table)
    
    try:
        _db.put_item(
            Item={
                'email': user,
                'type': 'developer',
                'created_at': int(time()),
            }
        )
    except Exception as e:
        return to_response_error(Errors.DB_WRITE_FAILED)
    
    sanitized_user = re.sub(r'[^a-zA-Z0-9._]', '-', user)
    if not _ssm:
        _ssm = SSM()
    if not _apig:
        _apig = boto3.client('apigateway')

    try:
        secret_key = str(uuid4())
        _ssm.set_param(
            f'/{stage}/developer/{sanitized_user}/secret_key',
            secret_key,
        )
    except Exception as e:
        print(f"Failed to write secret key to SSM: {e}")
        return to_response_error(Errors.SSM_WRITE_FAILED)

    try:
        usage_plan_params = _ssm.load_params(usage_plans_path)
        default_usage_plan_id = usage_plan_params.get('default', {}).get('id', None)

        api_key_value = str(uuid4())
        api_key_response = _apig.create_api_key(
            name=user,
            value=api_key_value,
            enabled=True
        )

        api_key_id = api_key_response.get('id')

        _apig.create_usage_plan_key(
            usagePlanId=default_usage_plan_id,
            keyId=api_key_id,
            keyType='API_KEY'
        )
    except Exception as e:
        print(f"Failed to create API key: {e}")
        return to_response_error(Errors.API_KEY_CREATION_FAILED)

    return to_response_success({
        'success': True
    })
