import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import List

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client.neo4j import Neo4j
from app.client.open_ai import OpenAI
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB,
                                        ParentChildItem, UserIntegrationItem)
from app.client.pinecone import Pinecone
from app.client.secrets import Secrets
from app.client.spacy import Spacy
from app.fetcher.base import DiscoveryResponse, Fetcher, FetchResponse
from app.mystery.ingestor import IngestInput, Ingestor, IngestResponse

db: ParentChildDB = None
secrets: Secrets = None

def handler(event: dict, context):
    global db, secrets

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']
    graph_db_uri: str = os.environ['GRAPH_DB_URI']

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)
    
    if not db:
        db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    if not secrets:
        secrets = Secrets(stage)

    user_integration_items: List[UserIntegrationItem] = db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    fetchers: List[Fetcher] = []
    upload_item = None 
    if user_integration_items and len(user_integration_items) > 0:
        for item in user_integration_items:
            integration = item.get_raw_child()
            if integration and integration == 'upload':
                upload_item = item
            else:
                fetchers.append(Fetcher.create(item.get_raw_child(), {
                    'client_id': secrets.get(f'{item.get_raw_child()}/CLIENT_ID'),
                    'client_secret': secrets.get(f'{item.get_raw_child()}/CLIENT_SECRET'),
                    'access_token': item.access_token,
                    'refresh_token': item.refresh_token,
                    'expiry_timestamp': item.expiry_timestamp
                }, last_fetch_timestamp=item.last_fetch_timestamp))
    fetchers.append(Fetcher.create('upload', {
        'bucket': upload_item_bucket,
        'prefix': f'{user}/'
    }, last_fetch_timestamp=upload_item.last_fetch_timestamp if upload_item else None))


    openai = OpenAI(api_key=secrets.get('OPENAI_API_KEY'))
    neo4j = Neo4j(uri=graph_db_uri, user=secrets.get('GRAPH_DB_KEY'), password=secrets.get('GRAPH_DB_SECRET'))
    pinecone = Pinecone(api_key=secrets.get('PINECONE_API_KEY'), environment='us-east1-gcp')
    ingestor = Ingestor(openai, neo4j, pinecone)
    timestamp = int(time())

    dfi_responses: List[DfiResponse] = []
    futures = None
    with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
        futures = [executor.submit(discover_fetch_ingest, user, fetcher, ingestor, timestamp) for fetcher in fetchers]
    if futures:
        for future in as_completed(futures):
            response_item = future.result()
            if response_item:
                dfi_responses.append(response_item)
    if len(dfi_responses) > 0:
        db_update_items = []
        for response in dfi_responses:
            if response.succeeded:
                db_update_items.append(ParentChildItem(
                    parent=f'{KeyNamespaces.USER.value}{user}',
                    child=f'{KeyNamespaces.INTEGRATION.value}{response.integration}',
                ))
        db.update(db_update_items, timestamp=timestamp, last_fetch_timestamp=timestamp)

    neo4j.close()
    return to_response_success({})

@dataclass
class DfiResponse:
    integration: str
    succeeded: bool

def discover_fetch_ingest(user: str, fetcher: Fetcher, ingestor: Ingestor, timestamp: int) -> DfiResponse:
    next_token: str = None
    succeeded: bool = True
    while True:
        discovery_response: DiscoveryResponse = fetcher.discover(next_token=next_token)
        if not (discovery_response and discovery_response.items):
            succeeded = False
            break
        next_token = discovery_response.next_token
        for item in discovery_response.items:
            fetch_response: FetchResponse = fetcher.fetch(item.id)
            if not fetch_response:
                succeeded = False
                continue
            ingest_input = IngestInput(
                owner=user,
                integration=fetcher._INTEGRATION,
                item_id=item.id,
                chunks=fetch_response.chunks,
                timestamp=timestamp
            )
            ingest_response: IngestResponse = ingestor.ingest(ingest_input)
            if not ingest_response.succeeded:
                succeeded = False
                continue

    return DfiResponse(integration=fetcher._INTEGRATION, succeeded=succeeded)
