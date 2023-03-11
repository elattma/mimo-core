import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import List

from app.db.pc import (KeyNamespaces, ParentChildDB, ParentChildItem,
                       UserIntegrationItem)
from app.fetcher.base import Fetcher, FetchResponse
from app.graph.blocks import (CONSISTS_OF, REFERENCES, Chunk, Document,
                              ProperNoun)
from app.graph.db import GraphDB
from app.util.embed import get_embedding
from app.util.ner import NER
from app.util.pinecone import Pinecone
from app.util.response import Errors, to_response_error, to_response_success
from app.util.secret import Secret
from ulid import ulid


def handler(event: dict, context):
    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']
    graph_db_uri: str = os.environ['GRAPH_DB_URI']

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)
    
    db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    secrets = Secret(stage)

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
            }), last_fetch_timestamp=item.last_fetch_timestamp)
    fetchers.append(Fetcher.create('upload', {
        'bucket': upload_item_bucket,
        'prefix': f'{user}/'
    }))

    timestamp = int(time())
    graph_db = GraphDB(uri=graph_db_uri, user=secrets.get('GRAPH_DB_KEY'), password=secrets.get('GRAPH_DB_SECRET'))
    pinecone = Pinecone(api_key=secrets.get('PINECONE_API_KEY'), environment='us-east1-gcp')
    ner = NER()
    openai_api_key = secrets.get('OPENAI_API_KEY')
    index_responses: List[IndexResponse] = []
    futures = None
    with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
        futures = [executor.submit(discover_fetch_embed_load, user, fetcher, graph_db, pinecone, ner, openai_api_key) for fetcher in fetchers]

    if futures:
        for future in as_completed(futures):
            response_item = future.result()
            if response_item:
                index_responses.append(response_item)
    
    if len(index_responses) > 0:
        db_update_items = []
        for response in index_responses:
            if response.succeeded:
                db_update_items.append(ParentChildItem(
                    parent=f'{KeyNamespaces.USER.value}{user}',
                    child=f'{KeyNamespaces.INTEGRATION.value}{response.integration}',
                ))
        db.update(db_update_items, timestamp=timestamp)

    return to_response_success({})

#TODO: refactor to something nicer. 1) grab some documents, 2a) embed, 2b) get proper nouns, 4) insert into db
@dataclass
class IndexResponse:
    succeeded: bool
    integration: str
    timestamp: int

def discover_fetch_embed_load(user: str, fetcher: Fetcher, db: GraphDB, pinecone: Pinecone, ner: NER, openai_api_key: str) -> IndexResponse:
    timestamp = int(time())
    next_token: str = None
    succeeded = True
    try:
        while True:
            # TODO: add pagination
            discovery_response = fetcher.discover()
            next_token = discovery_response.next_token
            documents: List[Document] = []
            if not (discovery_response and discovery_response.items):
                return False
            for item in discovery_response.items:
                fetch_response: FetchResponse = fetcher.fetch(item.id)
                if fetch_response:
                    chunks: List[Chunk] = []
                    for chunk in fetch_response.chunks:
                        embedding = get_embedding(openai_api_key, chunk.content)
                        entities = ner.get_entities(chunk.content)
                        proper_nouns = [ProperNoun(id=entity.text, user=user, type=entity.label_) for entity in entities]
                        chunks.append(Chunk(
                            id=ulid(),
                            user=user,
                            embedding=embedding,
                            content=chunk.content, 
                            type="text", 
                            references=[REFERENCES(target=proper_noun) for proper_noun in proper_nouns]
                        ))
                document = Document(
                    id=item.id,
                    user=user,
                    integration=fetcher._INTEGRATION,
                    consists_of=[CONSISTS_OF(target=chunk) for chunk in chunks]
                )
                documents.append(document)

            pinecone_response = pinecone.upsert(documents=documents, user=user, timestamp=timestamp)
            response = db.create_documents(documents=documents, user=user, timestamp=timestamp)
            if not next_token:
                break
    except Exception as e:
        print(e)
        print(fetcher._INTEGRATION)
        succeeded = False

    return IndexResponse(succeeded=succeeded, integration=fetcher._INTEGRATION, timestamp=timestamp)