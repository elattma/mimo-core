import re
from dataclasses import dataclass
from typing import Mapping

import boto3


@dataclass
class Integration:
    id: str = ''
    name: str = ''
    description: str = ''
    icon: str = ''
    oauth2_link: str = ''
    authorized: bool = False

class SSM:
    integrations: Mapping[str, Integration] = None

    def __init__(self, path: str) -> None:
        if not self.integrations:
            integrations: Mapping[str, Integration] = {}
            ssm_client = boto3.client('ssm')
            next_token = None
            while True:
                response = ssm_client.get_parameters_by_path(
                    Path=path,
                    Recursive=True,
                    **({'NextToken': next_token} if next_token is not None else {})
                )
                next_token = response.get('NextToken')

                for parameter in response['Parameters']:
                    id, key = re.search(r'/\w+/\w+/\w+/(\w+)/(\w+)', parameter.get('Name')).groups()
                    value = parameter.get('Value')
                    if id and key and value:
                        if not integrations.get(id, None):
                            integrations[id] = Integration(**{f'{key}': value})
                        else:
                            setattr(integrations.get(id), key, value)
                if next_token is None:
                    break
            self.integrations = integrations