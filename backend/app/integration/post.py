import json
import os
import time

from app.db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from app.fetcher.base import Fetcher
from app.util.response import Errors, to_response_error, to_response_success
from app.util.secret import Secret


def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    id = body.get('id', None) if body else None
    code = body.get('code', None) if body else None
    redirect_uri = body.get('redirect_uri', None) if body else None

    if not (user and stage and body and id and redirect_uri):
        return to_response_error(Errors.MISSING_PARAMS.value)

    secrets = Secret(stage)
    fetcher: Fetcher = Fetcher.create(id, {
        'client_id': secrets.get(f'{id}/CLIENT_ID'),
        'client_secret': secrets.get(f'{id}/CLIENT_SECRET')
    }) # TODO: split part of fetcher into integration

    succeeded = fetcher.auth.authorize({
        'code': code,
        'redirect_uri': redirect_uri
    })
    if not succeeded:
        return to_response_error(Errors.AUTH_FAILED.value)
    
    if fetcher.auth.access_token:
        db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
        parent = f'{KeyNamespaces.USER.value}{user}'
        child = f'{KeyNamespaces.INTEGRATION.value}{id}'
        try:
            db.write([UserIntegrationItem(parent, child, fetcher.auth.access_token, fetcher.auth.refresh_token, time(), fetcher.auth.expiry_timestamp)])
        except Exception as e:
            print(e)
            return to_response_error(Errors.DB_WRITE_FAILED.value)

    return to_response_success({})