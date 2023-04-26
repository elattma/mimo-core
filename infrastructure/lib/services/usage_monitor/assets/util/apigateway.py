from dataclasses import dataclass
from uuid import uuid4

import boto3


class ApiGateway:
    _apigateway = None

    def __init__(self, rest_api_id: str = None):
        if not self._apigateway:
            self._apigateway = boto3.client('apigateway')
        self._rest_api_id = rest_api_id
