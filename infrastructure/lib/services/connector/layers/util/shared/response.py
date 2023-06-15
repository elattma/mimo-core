import json
from enum import Enum

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

class Errors(Enum):
    INVALID_USER = 'invalid user'
    MISSING_PARAMS = 'missing params'
    MISSING_SECRETS = 'missing secrets'
    AUTH_FAILED = 'auth failed'
    DB_WRITE_FAILED = 'db write failed'
    OPENAI_ERROR = 'openai error'
    CHAT_ERROR = 'chat error'
    S3_ERROR = 's3 error'
    FAILED_DELETE_OLD_KEY = 'failed to delete old key'
    FAILED_CREATE_KEY = 'failed to create key'
    INVALID_AUTH = 'invalid auth'
    INVALID_CONNECTION = 'invalid connection'
    DB_READ_FAILED = 'db read failed'
    SYNC_IN_PROGRESS = 'sync in progress'
    BATCH_SUBMIT_FAILED = 'batch submit failed'
    CONNECTION_CREATION_FAILED = 'connection creation failed'
    DELETE_FAILED = 'delete failed'
    SFN_FAILED = 'sfn failed'

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