import os
from util.params import SSM

from util.apigateway import ApiGateway
from util.response import Errors, to_response_error, to_response_success

_api_params = None
_usage_plans_params = None

def handler(event: dict, context):
    global _api_params, _usage_plans_params

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
    usage_plan_id = _usage_plans_params.get('default', {}).get('id')
    api_id = _api_params.get('id', None)

    if not (user and stage and api_id):
        return to_response_error(Errors.MISSING_PARAMS)

    api_gateway = ApiGateway(rest_api_id=api_id)
    key_id = api_gateway.get_id(user, stage)
    single_day_usage = api_gateway.get_usage(usage_plan_id, key_id)

    if not single_day_usage:
        return to_response_error(Errors.FAILED_GET_USAGE, 500)

    return to_response_success({
        'usage': {
            'used': single_day_usage.used,
            'remaining': single_day_usage.remaining
        }
    })