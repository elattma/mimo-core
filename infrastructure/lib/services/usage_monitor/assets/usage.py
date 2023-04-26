import os

from util.apigateway import ApiGateway
from util.response import Errors, to_response_error, to_response_success

_api_params = None

def handler(event: dict, context):
    global _api_params

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    api_id = 'f3awvrk6y6'

    if not (user and stage and api_id):
        return to_response_error(Errors.MISSING_PARAMS)
    
    return to_response_success({})