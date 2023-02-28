import json
import os
import time
from typing import List, Mapping

import boto3
import requests
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.auth import refresh_token
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
secrets: Mapping[str, str] = None

def handler(event, context):
    global pc_db
    global secrets

    stage = os.environ['STAGE']
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not stage or not user:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId='{stage}/Mimo/Integrations'.format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)

    response_items = []
    for item in user_integration_items:
        integration = item.get_raw_child()
        if integration == 'google':
            client_id = secrets.get(f'{integration}/CLIENT_ID')
            client_secret = secrets.get(f'{integration}/CLIENT_SECRET')

            if not client_id or not client_secret:
                print(f'missing secrets for {integration}.. skipping!')
                continue
            
            access_token = refresh_token(db=pc_db, client_id=client_id, client_secret=client_secret, item=item)

            if not access_token:
                print(f'failed to refresh token for {integration}.. skipping!')
                continue

            response = requests.get(
                'https://www.googleapis.com/drive/v3/files',
                params={
                    'q': 'mimeType="application/vnd.google-apps.document" and trashed=false'
                },
                headers={
                    'Authorization': f'Bearer {access_token}'
                }         
            )
            # id title icon link optional(preview)
            print(response)

            # call google api to get data
            print('google')
            discovery_response = response.json()
            print(discovery_response)
            if not response or not discovery_response:
                print('failed to get google docs')
                continue 
            next_token = discovery_response.get('nextPageToken')
            files = discovery_response['files']
            response_items.append({
                'integration': integration,
                'icon': 'https://www.gstatic.com/images/branding/product/1x/drive_512dp.png',
                'items': [{
                    'id': file['id'],
                    'title': file['name'],
                    'link': f'https://docs.google.com/document/d/{file["id"]}',
                    'preview': file['thumbnailLink'] if 'thumbnailLink' in file else None
                } for file in files],
                'next_token': next_token
            })

    return to_response_success(response_items)