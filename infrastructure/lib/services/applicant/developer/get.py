import os
import re

from shared.response import Errors, to_response_error, to_response_success
from state.params import SSM

_ssm: SSM = None

def handler(event: dict, context):
    global _ssm

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    developer_secret_path_prefix: str = os.getenv('DEVELOPER_SECRET_PATH_PREFIX')

    if not (user and developer_secret_path_prefix):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _ssm:
        _ssm = SSM()

    user_sanitized = re.sub('[^a-zA-Z0-9._]', '-', user)
    path = '{prefix}/{user}'.format(prefix=developer_secret_path_prefix, user=user_sanitized)
    user_secrets = _ssm.load_params(path)
    if not user_secrets:
        return to_response_error(Errors.INVALID_DEVELOPER)
    
    secret_key = user_secrets.get('secret_key', None)
    return to_response_success({
        'secret_key': secret_key
    })
