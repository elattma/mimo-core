import json
import os
import time
from typing import Mapping

import boto3
import requests
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.constants import Integration
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
secrets: Mapping[str, str] = None

SOURCE_URI_MAP ={
    'slack': 'https://slack.com/api/oauth.v2.access',
    'google': 'https://oauth2.googleapis.com/token',
    'notion': 'https://api.notion.com/v1/oauth/token',
}

def handler(event, context):
    global pc_db
    global secrets

    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None
    stage = os.environ['STAGE']
    body = json.loads(event['body']) if event and event['body'] else None
    id = body['id'] if body else None
    code = body['code'] if body else None
    redirect_uri = body['redirect_uri'] if body else None
    integration_auth_uri = SOURCE_URI_MAP.get(id)

    if not user or not stage or not body or not id or not code or not redirect_uri or not integration_auth_uri:
        return to_response_error(Errors.MISSING_PARAMS)

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId='{stage}/Mimo/Integrations'.format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    client_id = secrets.get(f'{id}/CLIENT_ID')
    client_secret = secrets.get(f'{id}/CLIENT_SECRET')
    if not client_id or not client_secret:
        return to_response_error(Errors.MISSING_SECRETS)
    
    response = requests.post(
        integration_auth_uri, 
        data = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'access_type': 'offline',
        },
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        },
        auth = {
            'client_id': client_id,
            'client_secret': client_secret,
        }
    )
    print(response)

    auth_response = response.json() if response else None
    if not response or response.status_code != 200 or not auth_response or not auth_response['access_token']:
        print("failed auth call!")
        return to_response_error(Errors.AUTH_FAILED)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    parent = f'{KeyNamespaces.USER.value}{user}'
    child = f'{KeyNamespaces.INTEGRATION.value}{id}'
    access_token = auth_response['access_token']
    refresh_token = auth_response['refresh_token']
    timestamp = int(time.time())
    expiry_timestamp = auth_response['expires_in'] + timestamp if auth_response['expires_in'] else None
    try:
        pc_db.write([UserIntegrationItem(parent, child, access_token, refresh_token, timestamp, expiry_timestamp)])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({})