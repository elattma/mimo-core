import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client._secrets import Secrets
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB,
                                        UserIntegrationItem)
from app.fetcher.base import DiscoveryResponse, Fetcher

db: ParentChildDB = None
secrets: Secrets = None

def handler(event: dict, context):
    global db, secrets

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not db:
        db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    if not secrets:
        secrets = Secrets(stage)

    user_integration_items: List[UserIntegrationItem] = db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    fetchers: List[Fetcher] = []
    if user_integration_items and len(user_integration_items) > 0:
        for item in user_integration_items:
            fetchers.append(Fetcher.create(item.get_raw_child(), {
                'client_id': secrets.get(f'{item.get_raw_child()}/CLIENT_ID'),
                'client_secret': secrets.get(f'{item.get_raw_child()}/CLIENT_SECRET'),
                'access_token': item.access_token,
                'refresh_token': item.refresh_token,
                'expiry_timestamp': item.expiry_timestamp
            }))
    fetchers.append(Fetcher.create('upload', {
        'bucket': upload_item_bucket,
        'prefix': f'{user}/'
    }))

    response_items: List[DiscoveryResponse] = []
    futures = None
    with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
        futures = []
        for fetcher in fetchers:
            if fetcher:
                futures.append(executor.submit(fetcher.discover))

    if futures:
        for future in as_completed(futures):
            response_item = future.result()
            if response_item:
                response_items.append(response_item)

    return to_response_success([response_item.__dict__ for response_item in response_items])