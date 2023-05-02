import json
import os
from time import time
from typing import List

from auth.authorizer import Authorizer
from fetcher.base import Fetcher, Filter
from shared.model import AuthType, Connection
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB, UserConnectionItem
from state.params import SSM
from state.secrets import Secrets

_db: ParentChildDB = None
_secrets: Secrets = None
_integrations_dict: dict = None

def handler(event: dict, context):
    global _db, _secrets, _integrations_dict

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.getenv('STAGE')
    integrations_path: str = os.getenv('INTEGRATIONS_PATH')
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    connection: str = body.get('connection', None) if body else None

    if not (user and stage and connection):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _secrets:
        _secrets = Secrets(stage)
    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    if not _integrations_dict:
        ssm = SSM()
        _integrations_dict = ssm.load_nested_params(integrations_path)
    
    parent = f'{KeyNamespaces.USER.value}{user}'
    child = f'{KeyNamespaces.CONNECTION.value}{connection}'
    item: UserConnectionItem = _db.get(parent, child)
    connection: Connection = item.connection if item else None
    integration_id = connection.integration if connection else None
    integration = _integrations_dict.get(integration_id) if _integrations_dict else None
    if not (connection and connection.is_valid() and integration):
        return to_response_error(Errors.INVALID_CONNECTION)

    if connection.auth == AuthType.TOKEN_OAUTH2:
        integration_client_id = _secrets.get(f'{integration_id}/CLIENT_ID')
        integration_client_secret = _secrets.get(f'{integration_id}/CLIENT_SECRET')
        refresh_endpoint = integration.get('refresh_endpoint', None)
        strategy = TokenOAuth2Strategy(
            client_id=integration_client_id, 
            client_secret=integration_client_secret, 
            refresh_endpoint=refresh_endpoint
        )
        access_token = Authorizer.refresh(auth=connection.auth, strategy=strategy)

    fetcher: Fetcher = Fetcher.create(integration_id, access_token)
    max_pages = 20
    filter = Filter(limit=max_pages)
    response = fetcher.discover(filter)
    if not response:
        return to_response_error(Errors.DISCOVERY_ERROR)
    
    ingestion_timestamp = int(time())
    ingest_inputs: List[IngestInput] = []
    for page in response.pages:
        blocks_generator = fetcher.fetch(page)
        block_streams = [block_stream for block_stream in blocks_generator]
        ingest_input = IngestInput(
            owner=user,
            integration=integration_id,
            page_id=page.id,
            block_streams=block_streams,
            timestamp=ingestion_timestamp
        )
        ingest_inputs.append(ingest_input)
    ingestor.ingest(ingest_inputs)

    return to_response_success({
        'connection': connection.to_response()
    })
