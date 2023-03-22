import json
from decimal import Decimal
from enum import Enum

HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
}

class Errors(Enum):
    MISSING_PARAMS = 'missing params'
    MISSING_SECRETS = 'missing secrets'
    AUTH_FAILED = 'auth failed'
    DB_WRITE_FAILED = 'db write failed'
    OPENAI_ERROR = 'openai error'
    CHAT_ERROR = 'chat error'
    S3_ERROR = 's3 error'

def to_response_error(error_message: Errors = 'An error occurred'):
    return {
        'statusCode': 400,
        'headers': HEADERS,
        'body': json.dumps({
            'error': error_message
        })
    } 

class DecimalEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, Decimal):
      return str(obj)
    return json.JSONEncoder.default(self, obj)

def to_response_success(body: dict):
    return {
        'statusCode': 200,
        'headers': HEADERS,
        'body': json.dumps(body, cls=DecimalEncoder, default=lambda o: o.__dict__)
    }