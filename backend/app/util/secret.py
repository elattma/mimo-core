import json
from typing import Mapping

import boto3


class Secret:
    map: Mapping[str, str] = None

    def __init__(self, stage: str) -> None:
        if not self.map:
            secrets_client = boto3.client('secretsmanager')
            response = secrets_client.get_secret_value(SecretId='{stage}/Mimo/Integrations'.format(stage=stage))
            self.map = json.loads(response['SecretString'])

    def get(self, key: str) -> str:
        return self.map.get(key, None)