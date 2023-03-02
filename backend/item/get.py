import json
import os
from typing import List, Mapping

import boto3
from data.docs import Docs
from data.fetcher import DiscoveryResponse, Fetcher
from data.upload import Upload
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.auth import refresh_token
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
secrets: Mapping[str, str] = None
s3_client = None

def handler(event: dict, context):
    global pc_db
    global secrets

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    if not secrets:
        secrets_client = boto3.client('secretsmanager')
        secrets = secrets_client.get_secret_value(SecretId='{stage}/Mimo/Integrations'.format(stage=stage))
        secrets = json.loads(secrets['SecretString'])

    if not s3_client:
        s3_client = boto3.client('s3')

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

    upload_fetcher = Upload(access_token=access_token, s3_client=s3_client, bucket=upload_item_bucket, prefix=user)
    upload_discovery_response = upload_fetcher.discover()
    if upload_discovery_response:
        response_items.append(upload_discovery_response)

    return to_response_success([response_item.__dict__ for response_item in response_items])