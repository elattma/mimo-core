import json
import os
from enum import Enum

import boto3
import requests
from pyparsing import Mapping
from utils.email_system import EmailSystem


class Secrets:
    map: Mapping[str, str] = None

    def __init__(self, stage: str, secret_id: str = 'Mimo/Integrations') -> None:
        if not self.map:
            secrets_client = boto3.client('secretsmanager')
            response = secrets_client.get_secret_value(SecretId=f'{stage}/{secret_id}')
            self.map = json.loads(response['SecretString'])

    def get(self, key: str) -> str:
        return self.map.get(key, None)

email_system: EmailSystem = None
secrets: Secrets = None

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
    global email_system, secrets
    if not secrets:
        secrets = Secrets(os.environ['STAGE'])
    verification_token = secrets.get('SLACK_VERIFICATION_TOKEN')

    if not verification_token:
        return to_response_error(Errors.NO_VERIFICATION_TOKEN.value)

    body = event.get('body', None) if event else None
    body = json.loads(body) if body else None

    if not body:
        return to_response_error(Errors.NO_BODY.value)
    
    type = body.get('type', None)
    if type == 'url_verification':
        if is_verified(verification_token, body):
            return to_response_success({'challenge': body.get('challenge', None)})
        else:
            return to_response_error(Errors.INVALID_VERIFICATION_TOKEN.value)
    elif type != 'event_callback':
        return to_response_error('Invalid type')
    
    access_token = secrets.get('SLACK_ACCESS_TOKEN')    
    event = body.get('event', None)
    text = event.get('text', None) if event else None
    channel = event.get('channel', None) if event else None
    channel_type = event.get('channel_type', None) if event else None
    bot_id = event.get('bot_id', None) if event else None
    if not bot_id and channel_type == 'im':
        if not email_system:
            openai_api_key = secrets.get('OPENAI_API_KEY')
            mimo_test_token = os.environ.get('TEST_TOKEN', None)
            email_system = EmailSystem(
                openai_api_key=openai_api_key,
                mimo_test_token=mimo_test_token
            )
        
        message = {
            'channel': channel,
            'text': 'Give me just a few moments :)'
        }
        response = requests.get('https://slack.com/api/chat.postMessage', params=message, headers={
            'Authorization': f'Bearer {access_token}', 
            'Content-type': 'application/x-www-form-urlencoded'
        })
        response = response.json() if response else None
        if not (response and response.get('ok', False)):
            return to_response_error(response.get('error', 'An error occurred'))

        response = email_system.run(text)
        blocks = [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*To*: {response.recipient}'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*Subject*: {response.subject}'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'{response.body}'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': 'I created a prepopulated email for you. Click the button to open it.'
                },
                'accessory': {
                    'type': 'button',
                    'text': {
                        'type': 'plain_text',
                        'text': 'Open'
                    },
                    'value': 'open_email',
                    'url': f'{response.link}',
                    'action_id': 'open_email'
                }
            }
        ]

        message = {
            'channel': channel,
            'blocks': json.dumps(blocks)
        }
        response = requests.get('https://slack.com/api/chat.postMessage', params=message, headers={
            'Authorization': f'Bearer {access_token}', 
            'Content-type': 'application/x-www-form-urlencoded'
        })
        response = response.json() if response else None
        if response and response.get('ok', False):
            return to_response_success(response)
        else:
            return to_response_error(response.get('error', 'An error occurred'))
    
    return to_response_success({
        'message': 'Is bot or not a direct message'
    })
