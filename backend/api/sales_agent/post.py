from enum import Enum
import json
import os

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

class Errors(Enum):
    NO_VERIFICATION_TOKEN = 'no verification token'
    NO_BODY = 'no body'
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

def is_verified(verification_token: str, body: dict):
    return body.get('token', None) == verification_token

def handler(event: dict, context):
    print(event)
    print(context)
    verification_token = os.environ['VERIFICATION_TOKEN']

    if not verification_token:
        return to_response_error(Errors.NO_VERIFICATION_TOKEN.value)

    body = event.get('body', None) if event else None
    body = json.loads(body) if body else None

    if not body:
        return to_response_error(Errors.NO_BODY.value)
    
    type = body.get('type', None)
    if type:
        if is_verified(verification_token, body):
            return to_response_success({'challenge': body.get('challenge', None)})
        else:
            return to_response_error(Errors.INVALID_VERIFICATION_TOKEN.value)
    
    return to_response_success({
        'message': 'Hello World from slack bot'
    })
