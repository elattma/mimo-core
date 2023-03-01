import json
import os
from typing import List, Mapping

import boto3
from data.docs import Docs
from data.fetcher import DiscoveryResponse, Fetcher
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.auth import refresh_token
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
secrets: Mapping[str, str] = None

def handler(event, context):
    global pc_db
    global secrets

    user = event['requestContext']['authorizer']['principalId'] if event and 'requestContext' in event and 'authorizer' in event['requestContext'] and 'principalId' in event['requestContext']['authorizer'] else None
    stage = os.environ['STAGE']

    if not user or not stage:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    if secrets is None:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId='{stage}/Mimo/Integrations'.format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)

    response_items: List[DiscoveryResponse] = []
    for item in user_integration_items:
        integration = item.get_raw_child()
        client_id = secrets.get(f'{integration}/CLIENT_ID')
        client_secret = secrets.get(f'{integration}/CLIENT_SECRET')
        if not client_id or not client_secret:
            print(f'missing secrets for {integration}.. skipping!')
            continue
        access_token = refresh_token(db=pc_db, client_id=client_id, client_secret=client_secret, item=item)
        if not access_token:
            print(f'failed to refresh token for {integration}.. skipping!')
            continue
        data_fetcher: Fetcher = None
        if integration == 'google':
            data_fetcher = Docs(access_token=access_token)
        discovery_response = data_fetcher.discover()
        if discovery_response:
            response_items.append(discovery_response)

    return to_response_success([response_item.__dict__ for response_item in response_items])