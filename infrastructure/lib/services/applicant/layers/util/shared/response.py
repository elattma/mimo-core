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
    DB_WRITE_FAILED = 'db write failed'
    DB_READ_FAILED = 'db read failed'
    APP_LIMIT_REACHED = 'app limit reached'
    APP_NOT_FOUND = 'app not found'
    INVALID_TOKEN = 'invalid token'
    LIBRARY_NOT_FOUND = 'library not found'
    INVALID_DEVELOPER = 'invalid developer'
    TOKEN_EXPIRED = 'token expired'
    GENERATE_SECRET_KEY_FAILED = 'generate secret key failed'
    MISSING_UPDATE_PARAMS = 'missing update params'

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