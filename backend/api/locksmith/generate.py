import json
import os

from aws.apigateway import ApiGateway
from aws.response import Errors, to_response_error, to_response_success


def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    rest_api_id: str = os.getenv('REST_API_ID')
    default_usage_plan_id: str = os.getenv('DEFAULT_USAGE_PLAN_ID')

    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    user_defined_name: str = body.get('user_defined_name', None) if body else None

    if not (user and stage and rest_api_id):
        return to_response_error(Errors.MISSING_PARAMS)
    
    api_locksmith = ApiGateway(rest_api_id=rest_api_id)
    old_api_key = api_locksmith.get(user, stage)
    if old_api_key:
        succeded = api_locksmith.delete(old_api_key)
        if not succeded:
            return to_response_error(Errors.FAILED_DELETE_OLD_KEY.value)
    api_key = api_locksmith.generate(
        usage_plan_id=default_usage_plan_id,
        user=user,
        stage=stage,
        user_defined_name=user_defined_name,
    )
    if not api_key:
        return to_response_error(Errors.FAILED_CREATE_KEY.value)

    return to_response_success({
        'apiKey': {
            'value': api_key.value,
        }
    })
