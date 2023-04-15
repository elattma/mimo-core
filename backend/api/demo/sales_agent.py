import json
import os

import requests
from utils.common import (Errors, Secrets, to_response_error,
                          to_response_success)
from utils.email_system import EmailSystem
from utils.model import EmailSystemError, EmailSystemResponse

email_system: EmailSystem = None
secrets: Secrets = None

def handler(event: dict, context):
    print(event)
    print(context)
    global email_system, secrets
    if not secrets:
        secrets = Secrets(os.environ['STAGE'])
    access_token = secrets.get('SLACK_ACCESS_TOKEN')
    records = event.get('Records', None) if event else None
    if not records:
        return to_response_error(Errors.NO_RECORDS.value)
    
    if not email_system:
        openai_api_key = secrets.get('OPENAI_API_KEY')
        mimo_test_token = os.environ.get('TEST_TOKEN', None)
        email_system = EmailSystem(
            openai_api_key=openai_api_key,
            mimo_test_token=mimo_test_token
        )

    for record in records:
        body = record.get('body', None) if record else None
        body = json.loads(body) if body else None

        if not body:
            continue
        
        text = body.get('text', None) if body else None
        channel = body.get('channel', None) if body else None

        system_response: EmailSystemResponse = email_system.run(text)
        if isinstance(system_response, EmailSystemError):
            chat_response = requests.get('https://slack.com/api/chat.postMessage', 
                params={
                    'channel': channel,
                    'text': system_response.message
                },
                headers={
                    'Authorization': f'Bearer {access_token}', 
                    'Content-type': 'application/x-www-form-urlencoded'
                }
            )
        else:
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

            chat_response = requests.get('https://slack.com/api/chat.postMessage', 
                params={
                    'channel': channel,
                    'blocks': json.dumps(blocks)
                },
                headers={
                    'Authorization': f'Bearer {access_token}', 
                    'Content-type': 'application/x-www-form-urlencoded'
                }
            )
            chat_response = chat_response.json() if chat_response else None
            print(chat_response)
    return to_response_success(chat_response)
    