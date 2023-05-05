import os
from typing import Any, Dict, List

from shared.model import Integration
from shared.response import Errors, to_response_error, to_response_success
from state.params import SSM

_integrations: List[Integration] = None

def handler(_, __):
    global _integrations

    integrations_path: str = os.getenv('INTEGRATIONS_PATH')

    if not integrations_path:
        return to_response_error(Errors.MISSING_PARAMS)

    if not _integrations:
        _ssm = SSM()
        integrations: Dict[str, Any] = _ssm.load_params(integrations_path)
        _integrations = [Integration.from_dict(integration_params) for integration_params in integrations.values()]
    
    return to_response_success({
        'integrations': [{
            'id': integration.id,
            'name': integration.name,
            'description': integration.description,
            'icon': integration.icon,
            'auth_strategies': [{
                'type': type.value,
                'params': strategy.get_params()
            } for type, strategy in integration.auth_strategies.items()]
        } for integration in _integrations],
        'next_token': None
    })
