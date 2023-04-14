import json
from enum import Enum
from typing import Mapping

import boto3


class Secrets:
    _map: Mapping[str, str] = None

    def __init__(self, stage: str, secret_id: str = 'Mimo/Integrations') -> None:
        if not self._map:
            secrets_client = boto3.client('secretsmanager')
            response = secrets_client.get_secret_value(SecretId=f'{stage}/{secret_id}')
            self._map = json.loads(response['SecretString'])

    def get(self, key: str) -> str:
        return self._map.get(key, None)
    
HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

class Errors(Enum):
    NO_VERIFICATION_TOKEN = 'no verification token'
    MISSING_PARAMS = 'missing params'
    NO_BODY = 'no body'
    NO_RECORDS = 'no records'
    INVALID_VERIFICATION_TOKEN = 'invalid verification token'

def to_response_error(error_message: Errors = 'An error occurred'):
    return {
        'statusCode': 400,
        'headers': HEADERS,
        'body': json.dumps({
            'error': error_message
        })
    } 

def to_response_success(body: dict):
    return {
        'statusCode': 200,
        'headers': HEADERS,
        'body': json.dumps(body, default=lambda o: o.__dict__)
    }