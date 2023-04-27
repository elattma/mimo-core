import os
from typing import Dict, List

from util.model import Integration
from util.params import SSM
from util.response import Errors, to_response_error, to_response_success

_integrations: List[Integration] = None

def handler(event: dict, context):
    global _integrations

    integrations_path: str = os.getenv('INTEGRATIONS_PATH')

    if not integrations_path:
        return to_response_error(Errors.MISSING_PARAMS)

    if not _integrations:
        _ssm = SSM()
        integrations: Dict[str, dict] = _ssm.load_nested_params(integrations_path)
        _integrations = [Integration(**integration_params) for integration_params in integrations.values()]
    
    return to_response_success({
        'integrations': [integration.__dict__ for integration in _integrations],
        'next_token': None
    })