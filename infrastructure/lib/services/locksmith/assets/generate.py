import json
import os
from typing import Dict

from util.apigateway import ApiGateway
from util.model import UsagePlan
from util.params import SSM
from util.response import Errors, to_response_error, to_response_success

_usage_plans_params = None
_api_params = None

def handler(event: dict, context):
    global _usage_plans_params, _api_params

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    api_path: str = os.getenv('API_PATH')
    usage_plans_path: str = os.getenv('USAGE_PLANS_PATH')
    ssm = SSM()
    if not _usage_plans_params:
        _usage_plans_params = ssm.load_nested_params(usage_plans_path)
    if not _api_params:
        _api_params = ssm.load_params(api_path)
    default_usage_plan = UsagePlan(**_usage_plans_params.get('default', {}))
    api_id = _api_params.get('id', None)

    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    user_defined_name: str = body.get('user_defined_name', None) if body else None

    print(user)
    print(stage)
    print(api_id)
    print(default_usage_plan.id)
    if not (user and stage and api_id and default_usage_plan.id):
        return to_response_error(Errors.MISSING_PARAMS)
    
    api_locksmith = ApiGateway(rest_api_id=api_id)
    old_api_key = api_locksmith.get(user, stage)
    if old_api_key:
        succeded = api_locksmith.delete(old_api_key)
        if not succeded:
            return to_response_error(Errors.FAILED_DELETE_OLD_KEY)
    api_key = api_locksmith.generate(
        usage_plan_id=default_usage_plan.id,
        user=user,
        stage=stage,
        user_defined_name=user_defined_name,
    )
    if not api_key:
        return to_response_error(Errors.FAILED_CREATE_KEY)

    return to_response_success({
        'apiKey': {
            'value': api_key.value,
        }
    })
