import sys

sys.path.append('/Users/mo/workplace/mimo/backend/layers/aws')
sys.path.append('/Users/mo/workplace/mimo/backend/layers/mystery')
sys.path.append('/Users/mo/workplace/mimo/backend/layers/external')
sys.path.append('/Users/mo/workplace/mimo/backend/layers/graph')
sys.path.append('/Users/mo/workplace/mimo/backend/layers/fetcher')

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import List

from aws.dynamo import (KeyNamespaces, ParentChildDB, ParentChildItem,
                        UserIntegrationItem)
from aws.response import Errors, to_response_error, to_response_success
from aws.secrets import Secrets
from external.openai_ import OpenAI
from fetcher.base import DiscoveryResponse, Fetcher, Filter
from graph.blocks import BlockStream
from graph.neo4j_ import Neo4j
from graph.pinecone_ import Pinecone
from mystery.ingestor import IngestInput, Ingestor, IngestResponse

db: ParentChildDB = None
secrets: Secrets = None

def handler(event: dict, context):
    global db, secrets

    request_context: dict = event.get("requestContext", None) if event else None
    authorizer: dict = (
        request_context.get("authorizer", None) if request_context else None
    )
    user: str = authorizer.get("principalId", None) if authorizer else None
    stage: str = os.environ["STAGE"]
    upload_item_bucket: str = os.environ["UPLOAD_ITEM_BUCKET"]
    graph_db_uri: str = os.environ["GRAPH_DB_URI"]

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not db:
        db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))
    if not secrets:
        secrets = Secrets(stage)

    user_integration_items: List[UserIntegrationItem] = db.query(
        "{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user),
        child_namespace=KeyNamespaces.INTEGRATION.value,
        Limit=100,
    )
    fetchers: List[Fetcher] = []
    if user_integration_items and len(user_integration_items) > 0:
        for item in user_integration_items:
            integration = item.get_raw_child()
            if integration == 'zendesk':
                continue
            fetchers.append(Fetcher.create(integration, {
                'client_id': secrets.get(f'{item.get_raw_child()}/CLIENT_ID'),
                'client_secret': secrets.get(f'{item.get_raw_child()}/CLIENT_SECRET'),
                'access_token': item.access_token,
                'refresh_token': item.refresh_token,
                'expiry_timestamp': item.expiry_timestamp
            }, last_fetch_timestamp=item.last_fetch_timestamp))

    openai = OpenAI(api_key=secrets.get("OPENAI_API_KEY"))
    neo4j = Neo4j(
        uri=graph_db_uri,
        user=secrets.get("GRAPH_DB_KEY"),
        password=secrets.get("GRAPH_DB_SECRET"),
    )
    pinecone = Pinecone(
        api_key=secrets.get("PINECONE_API_KEY"), environment="us-east1-gcp"
    )
    ingestor = Ingestor(openai, neo4j, pinecone)
    timestamp = int(time())

    dfi_responses: List[DfiResponse] = []
    futures = None
    if not fetchers:
        return to_response_success({})
    with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
        futures = [
            executor.submit(discover_fetch_ingest, user, fetcher, ingestor, timestamp)
            for fetcher in fetchers
        ]
    if futures:
        for future in as_completed(futures):
            response_item = future.result()
            if response_item:
                dfi_responses.append(response_item)
    if len(dfi_responses) > 0:
        db_update_items = []
        for response in dfi_responses:
            if response.succeeded:
                db_update_items.append(
                    ParentChildItem(
                        parent=f"{KeyNamespaces.USER.value}{user}",
                        child=f"{KeyNamespaces.INTEGRATION.value}{response.integration}",
                    )
                )
        db.update(db_update_items, timestamp=timestamp, last_fetch_timestamp=timestamp)

    neo4j.close()
    return to_response_success({})

@dataclass
class DfiResponse:
    integration: str
    succeeded: bool

def discover_fetch_ingest(
    user: str, fetcher: Fetcher, ingestor: Ingestor, timestamp: int
) -> DfiResponse:
    max_items = 2000 # TODO: remove once ready
    next_token: str = None
    succeeded: bool = True
    while True: 
        filter = Filter(next_token=next_token)
        discovery_response: DiscoveryResponse = fetcher.discover(filter=filter)
        if not (discovery_response and discovery_response.items):
            succeeded = False
            break
        next_token = discovery_response.next_token
        for item in discovery_response.items:
            max_items -= 1
            ingestion_timestamp = int(time())
            blocks_generator = fetcher.fetch(item.id)

            block_streams: List[BlockStream] = []
            for block_stream in blocks_generator:
                block_streams.append(block_stream)
            ingest_input = IngestInput(
                owner=user,
                integration=fetcher._INTEGRATION,
                document_id=item.id,
                block_streams=block_streams,
                timestamp=ingestion_timestamp
            )
            ingest_response: IngestResponse = ingestor.ingest(ingest_input)
            if not ingest_response.succeeded:
                succeeded = False
                continue
            if max_items <= 0:
                return DfiResponse(integration=fetcher._INTEGRATION, succeeded=succeeded)
        if not next_token:
            break

    return DfiResponse(integration=fetcher._INTEGRATION, succeeded=succeeded)


event = {
    "requestContext": {
        "authorizer": {
            "principalId": "google-oauth2|108573573074253667565"
        }
    },
}

os.environ['AWS_PROFILE'] = 'mimo'
os.environ['STAGE'] = 'beta'
os.environ['UPLOAD_ITEM_BUCKET'] = 'mimo-beta-upload-item'
os.environ['GRAPH_DB_URI'] = 'neo4j+s://67eff9a1.databases.neo4j.io'
handler(event, None)