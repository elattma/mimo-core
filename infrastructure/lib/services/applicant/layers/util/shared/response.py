import json
from enum import Enum

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

class Errors(Enum):
    MISSING_PARAMS = 'missing params'
    INVALID_DEVELOPER = 'invalid developer'

def to_response_error(error_message: Errors):
    return {
        'statusCode': 400,
        'headers': HEADERS,
        'body': json.dumps({
            'error': error_message.value
        })
    } 

def to_response_success(body: dict):
    return {
        'statusCode': 200,
        'headers': HEADERS,
        'body': json.dumps(body, default=lambda o: o.__dict__)
    }