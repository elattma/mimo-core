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
        items = usage_response.get('items', None)
        try:
            todays_usage = items[0]
            used = todays_usage[0]
            remaining = todays_usage[1]
        except Exception as e:
            print(e)
            raise Exception('Failed to get usage information')
        usage_day = SingleDayUsage(used, remaining)
        return usage_day