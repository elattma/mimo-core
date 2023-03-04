import os
from typing import List

from app.db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from app.fetcher.base import DiscoveryResponse, Fetcher
from app.util.response import Errors, to_response_error, to_response_success
from app.util.secret import Secret


def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)

    db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    secrets = Secret(stage)

    user_integration_items: List[UserIntegrationItem] = db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    fetchers: List[Fetcher] = []
    if user_integration_items and len(user_integration_items) > 0:
        for item in user_integration_items:
            fetcher = Fetcher.create(item.get_raw_child(), {
                'client_id': secrets.get(f'{item.get_raw_child()}/CLIENT_ID'),
                'client_secret': secrets.get(f'{item.get_raw_child()}/CLIENT_SECRET'),
                'access_token': item.access_token,
                'refresh_token': item.refresh_token,
                'expiry_timestamp': item.expiry_timestamp
            })
            print(fetcher)
            fetchers.append(fetcher)
    fetcher = Fetcher.create('upload', {
        'bucket': upload_item_bucket,
        'prefix': user
    })
    print(fetcher)
    print(fetcher.auth)
    print(fetcher)
    fetchers.append(fetcher)

    response_items: List[DiscoveryResponse] = []
    for fetcher in fetchers:
        response = fetcher.discover()
        if response:
            response_items.append(response)
    
    return to_response_success([response_item.__dict__ for response_item in response_items])