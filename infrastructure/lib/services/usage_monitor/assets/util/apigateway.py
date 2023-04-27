from dataclasses import dataclass
from datetime import datetime

import boto3


@dataclass
class SingleDayUsage:
    used: int
    remaining: int

class ApiGateway:
    _apigateway = None

    def __init__(self, rest_api_id: str = None):
        if not self._apigateway:
            self._apigateway = boto3.client('apigateway')
        self._rest_api_id = rest_api_id

    def _get_api_key_name(self, user: str, stage: str) -> str:
        return f'{stage}-{user}'

    def get_id(self, user: str, stage: str) -> str:
        response = self._apigateway.get_api_keys(
            nameQuery=self._get_api_key_name(user, stage),
            includeValues=True,
        )

        items = response.get('items', []) if response else []
        id = items[0].get('id', None) if items else None
        return id

    def get_usage(self, usage_plan_id: str, key_id: str) -> SingleDayUsage:
        todays_date = datetime.today().strftime('%Y-%m-%d')
        usage_response = self._apigateway.get_usage(
            usagePlanId=usage_plan_id,
            keyId=key_id,
            startDate=todays_date,
            endDate=todays_date,
        )
        if not usage_response:
            return None
        api_key_items = usage_response.get('items', {}).get(key_id, None) if usage_response else None
        todays_usage_item = api_key_items[0] if api_key_items else None
        if not todays_usage_item or len(todays_usage_item) < 2:
            return SingleDayUsage(used=0, remaining=100)
        usage = SingleDayUsage(used=todays_usage_item[0], remaining=todays_usage_item[1])
        return usage