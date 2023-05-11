import os
import re
from uuid import uuid4

from shared.response import Errors, to_response_error, to_response_success
from state.params import SSM

_ssm: SSM = None

def handler(event: dict, context):
    global _ssm

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    body: dict = event.get('body', None) if event else None
    regenerate_secret_key: bool = body.get('regenerate_secret_key', False) if body else False
    developer_secret_path_prefix: str = os.getenv('DEVELOPER_SECRET_PATH_PREFIX')

    if not (user and developer_secret_path_prefix):
        return to_response_error(Errors.MISSING_PARAMS)

    if regenerate_secret_key:
        if not _ssm:
            _ssm = SSM()

        user_sanitized = re.sub('[^a-zA-Z0-9._]', '-', user)
        path = '{prefix}/{user}'.format(prefix=developer_secret_path_prefix, user=user_sanitized)
        user_secrets = _ssm.load_params(path)
        secret_key = user_secrets.get('secret_key', None) if user_secrets else None
        if not secret_key:
            return to_response_error(Errors.INVALID_DEVELOPER)
        secret_key = regenerate_secret_key(path)
        if not secret_key:
            return to_response_error(Errors.GENERATE_SECRET_KEY_FAILED)
        return to_response_success({
            'secret_key': secret_key
        })
    
    return to_response_error(Errors.MISSING_UPDATE_PARAMS)

def regenerate_secret_key(ssm_path: str):
    global _ssm

    if not _ssm:
        _ssm = SSM()

    api_key_value = str(uuid4())
    succeeded = _ssm.set_param(ssm_path + '/secret_key', api_key_value)
    return api_key_value if succeeded else None
