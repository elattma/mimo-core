import os

from aws.apigateway import ApiGateway
from aws.response import Errors, to_response_error, to_response_success


def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    rest_api_id: str = os.getenv('REST_API_ID')

    if not (user and stage and rest_api_id):
        return to_response_error(Errors.MISSING_PARAMS)
    
    api_locksmith = ApiGateway(rest_api_id=rest_api_id)
    api_key = api_locksmith.get(user, stage)
    return to_response_success({
        'apiKey': {
            'value': api_key.value if api_key else None,
        }
    })