from dataclasses import dataclass
from uuid import uuid4

import boto3


@dataclass
class ApiKey:
    id: str
    value: str
    usage_plan_id: str
    user_defined_name: str


class ApiGateway:
    _apigateway = None

    def __init__(self, rest_api_id: str = None):
        if not self._apigateway:
            self._apigateway = boto3.client('apigateway')
        self._rest_api_id = rest_api_id

    def _get_new_key(self) -> str:
        return str(uuid4())
    
    def _get_api_key_name(self, user: str, stage: str) -> str:
        return f'{stage}-{user}'

    def generate(self, usage_plan_id: str, user: str, stage: str, user_defined_name: str = None) -> ApiKey:
        uuid = self._get_new_key()
        key_response = self._apigateway.create_api_key(
            name=self._get_api_key_name(user, stage),
            enabled=True,
            value=uuid,
            stageKeys=[{
                'restApiId': self._rest_api_id,
                'stageName': stage
            }],
            tags={
                'usage_plan_id': usage_plan_id,
                'user_defined_name': user_defined_name if user_defined_name else ''
            }
        )
        key_id = key_response.get('id', None)
        key_value = key_response.get('value', None)
        key_tags = key_response.get('tags', None)
        usage_plan_id = key_tags.get('usage_plan_id', None) if key_tags else None
        user_defined_name = key_tags.get('user_defined_name', None) if key_tags else None
        api_key = ApiKey(
            id=key_id, 
            value=key_value, 
            usage_plan_id=usage_plan_id,
            user_defined_name=user_defined_name
        ) if key_id and key_value and usage_plan_id else None

        if not api_key:
            raise Exception('failed to create api key')
        
        usage_response = self._apigateway.create_usage_plan_key(
            usagePlanId=usage_plan_id,
            keyId=api_key.id,
            keyType='API_KEY',
        )

        if not usage_response or usage_response.get('id', None) != api_key.id:
            self.delete(user, stage)
            raise Exception('failed to create usage plan key')

        return api_key
    
    def get(self, user: str, stage: str) -> ApiKey:
        response = self._apigateway.get_api_keys(
            nameQuery=self._get_api_key_name(user, stage),
            includeValues=True,
        )

        items = response.get('items', []) if response else []
        api_keys = [ApiKey(
            id=item.get('id', None), 
            value=item.get('value', None), 
            usage_plan_id=item.get('tags', {}).get('usage_plan_id'),
            user_defined_name=item.get('tags', {}).get('user_defined_name')
        ) for item in items] if items else []
        return api_keys[0] if api_keys else None
    
    def delete(self, api_key: ApiKey) -> bool:
        key_response = self._apigateway.delete_api_key(
            apiKey=api_key.id
        )

        return key_response is not None