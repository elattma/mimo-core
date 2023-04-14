import json
import os
from enum import Enum

import boto3
import requests
from pyparsing import Mapping
from utils.email_system import EmailSystem, EmailSystemSuccess


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
            return to_response_error(wait_response.get('error', 'An error occurred'))

        system_response: EmailSystemSuccess = email_system.run(text)
        blocks = [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*To*: {system_response.recipient}'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'*Subject*: {system_response.subject}'
                }
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'{system_response.body}'
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
                    'url': f'{system_response.link}',
                    'action_id': 'open_email'
                }
            }
        ]

        message = {
            'channel': channel,
            'blocks': json.dumps(blocks)
        }
        chat_response = requests.get('https://slack.com/api/chat.postMessage', params=message, headers={
            'Authorization': f'Bearer {access_token}', 
            'Content-type': 'application/x-www-form-urlencoded'
        })
        chat_response = chat_response.json() if chat_response else None
        if chat_response and chat_response.get('ok', False):
            return to_response_success(chat_response)
        else:
            return to_response_error(chat_response.get('error', 'An error occurred'))
    
    return to_response_success({
        'message': 'Is bot or not a direct message'
    })

event = {'version': '2.0', 'routeKey': '$default', 'rawPath': '/', 'rawQueryString': '', 'headers': {'content-length': '1375', 'x-amzn-tls-version': 'TLSv1.2', 'x-forwarded-proto': 'https', 'x-forwarded-port': '443', 'x-forwarded-for': '54.205.187.4', 'accept': '*/*', 'x-amzn-tls-cipher-suite': 'ECDHE-RSA-AES128-GCM-SHA256', 'x-amzn-trace-id': 'Root=1-6438cda6-069949fd68d0d6d97a1962c5', 'host': 'h6wtrhef5d6hhtzovni3eqtx4m0rzdht.lambda-url.us-east-1.on.aws', 'content-type': 'application/json', 'x-slack-request-timestamp': '1681444262', 'x-slack-signature': 'v0=2a4a191f1a61add6f068eebd28f82a76676978dbd26d8e9490d5dea7d6e16264', 'accept-encoding': 'gzip,deflate', 'user-agent': 'Slackbot 1.0 (+https://api.slack.com/robots)'}, 'requestContext': {'accountId': 'anonymous', 'apiId': 'h6wtrhef5d6hhtzovni3eqtx4m0rzdht', 'domainName': 'h6wtrhef5d6hhtzovni3eqtx4m0rzdht.lambda-url.us-east-1.on.aws', 'domainPrefix': 'h6wtrhef5d6hhtzovni3eqtx4m0rzdht', 'http': {'method': 'POST', 'path': '/', 'protocol': 'HTTP/1.1', 'sourceIp': '54.205.187.4', 'userAgent': 'Slackbot 1.0 (+https://api.slack.com/robots)'}, 'requestId': '3310818b-d8c1-4084-aef7-2e399eb98f0d', 'routeKey': '$default', 'stage': '$default', 'time': '14/Apr/2023:03:51:02 +0000', 'timeEpoch': 1681444262478}, 'body': '{"token":"7dMibSNCxREUyNPpE6STcyLL","team_id":"T03R7BR3RGF","context_team_id":"T03R7BR3RGF","context_enterprise_id":null,"api_app_id":"A052TNLPX1U","event":{"bot_id":"B053Q2PM7S4","type":"message","text":"Give me just a few moments :)","user":"U052KRAG4MV","ts":"1681444262.072099","app_id":"A052TNLPX1U","blocks":[{"type":"rich_text","block_id":"MZ6","elements":[{"type":"rich_text_section","elements":[{"type":"text","text":"Give me just a few moments :)"}]}]}],"team":"T03R7BR3RGF","bot_profile":{"id":"B053Q2PM7S4","deleted":false,"name":"Email Agent","updated":1681409978,"app_id":"A052TNLPX1U","icons":{"image_36":"https:\\/\\/avatars.slack-edge.com\\/2023-04-13\\/5104200659333_cdd707d22181402387da_36.png","image_48":"https:\\/\\/avatars.slack-edge.com\\/2023-04-13\\/5104200659333_cdd707d22181402387da_48.png","image_72":"https:\\/\\/avatars.slack-edge.com\\/2023-04-13\\/5104200659333_cdd707d22181402387da_72.png"},"team_id":"T03R7BR3RGF"},"channel":"D0532RVSDFE","event_ts":"1681444262.072099","channel_type":"im"},"type":"event_callback","event_id":"Ev0530M2L0LW","event_time":1681444262,"authorizations":[{"enterprise_id":null,"team_id":"T03R7BR3RGF","user_id":"U052KRAG4MV","is_bot":true,"is_enterprise_install":false}],"is_ext_shared_channel":false,"event_context":"4-eyJldCI6Im1lc3NhZ2UiLCJ0aWQiOiJUMDNSN0JSM1JHRiIsImFpZCI6IkEwNTJUTkxQWDFVIiwiY2lkIjoiRDA1MzJSVlNERkUifQ"}', 'isBase64Encoded': False}

os.environ['STAGE'] = 'beta'
os.environ['TEST_TOKEN'] = '82dab942-f0f4-4721-953d-200e0a750639'
mimo_test_token = os.environ.get('TEST_TOKEN', None)