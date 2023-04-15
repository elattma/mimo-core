import json
import os
from typing import Mapping

import boto3
import requests


def to_response_success(body: dict):
    return {
        'statusCode': 200,
        'headers': {
            'content-type': 'application/json'
        },
        'body': json.dumps(body)
    }

class Secrets:
    _map: Mapping[str, str] = None

    def __init__(self, stage: str, secret_id: str = 'Mimo/Integrations') -> None:
        if not self._map:
            secrets_client = boto3.client('secretsmanager', region_name='us-east-1')
            response = secrets_client.get_secret_value(SecretId=f'{stage}/{secret_id}')
            self._map = json.loads(response['SecretString'])

    def get(self, key: str) -> str:
        return self._map.get(key, None)

class Sqs:
    _sqs = None

    def __init__(self) -> None:
        if not self._sqs:
            self._sqs = boto3.client('sqs', region_name='us-east-1')
        
    def send_message(self, queue_url: str, message_body: dict):
        return self._sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )

IS_COLD_START = True
secrets: Secrets = None
sqs: Sqs = None

def handler(event: dict, context):
    print(event)
    print(context)
    global secrets, sqs, IS_COLD_START
    if not secrets:
        secrets = Secrets(os.environ['STAGE'])
    if not sqs:
        sqs = Sqs()
    verification_token = secrets.get('SLACK_VERIFICATION_TOKEN')

    if not verification_token:
        return to_response_success({
            'response_action': 'clear',
        })

    body = event.get('body', None) if event else None
    body = json.loads(body) if body else None
    test_token = os.environ['TEST_TOKEN']

    if not (body and test_token):
        return to_response_success({
            'response_action': 'clear',
        })
    
    type = body.get('type', None)
    if type == 'url_verification':
        if body.get('token', None) == verification_token:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
                },
                'body': json.dumps({
                    'challenge': body.get('challenge', None)
                })
            }
        else:
            return to_response_success({
                'response_action': 'clear',
            })
    elif type != 'event_callback':
        return to_response_success({
            'response_action': 'clear',
        })
    
    if IS_COLD_START:
        IS_COLD_START = False
        import time
        time.sleep(3)
        return 400

    access_token = secrets.get('SLACK_ACCESS_TOKEN')    
    event = body.get('event', None)
    text = event.get('text', None) if event else None
    channel = event.get('channel', None) if event else None
    channel_type = event.get('channel_type', None) if event else None
    bot_id = event.get('bot_id', None) if event else None
    subtype = event.get('subtype', None) if event else None
    if not bot_id and channel_type == 'im' and not subtype:
        wait_response = requests.get('https://slack.com/api/chat.postMessage', 
            params={
                'channel': channel,
                'text': 'Give me just a few moments :)'
            }, 
            headers={
                'Authorization': f'Bearer {access_token}', 
                'Content-type': 'application/x-www-form-urlencoded'
            }
        )
        wait_response = wait_response.json() if wait_response else None
        if not (wait_response and wait_response.get('ok', False)):
            return to_response_success({
                'response_action': 'clear',
            })

        agent_queue_url = os.environ['AGENT_QUEUE_URL']
        sqs.send_message(agent_queue_url, {
            'text': text,
            'channel': channel
        })
        print(f'Invoked {agent_queue_url}!')
    
    return to_response_success({
        'response_action': 'clear',
    })
