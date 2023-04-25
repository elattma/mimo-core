import os

from util.apigateway import ApiGateway
from util.params import SSM
from util.response import Errors, to_response_error, to_response_success

_api_params = None

def handler(event: dict, context):
    global _api_params

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    api_path: str = os.getenv('API_PATH')
    ssm = SSM()
    if not _api_params:
        _api_params = ssm.load_params(api_path)
    api_id = _api_params.get('id', None)

    if not (user and stage and api_id):
        return to_response_error(Errors.MISSING_PARAMS)
    
    api_locksmith = ApiGateway(rest_api_id=api_id)
    api_key = api_locksmith.get(user, stage)
    return to_response_success({
        'apiKey': {
            'value': api_key.value if api_key else None,
        }
    })