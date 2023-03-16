import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import time
from typing import List

from app.db.pc import (KeyNamespaces, ParentChildDB, ParentChildItem,
                       UserIntegrationItem)
from app.fetcher.base import Fetcher, FetchResponse
from app.graph.blocks import CONSISTS_OF, PREDICATES, Chunk, Document, Entity
from app.graph.db import GraphDB
from app.util.llm import get_embedding, get_knowledge_triplets, summarize
from app.util.ner import NER
from app.util.response import Errors, to_response_error, to_response_success
from app.util.secret import Secret
from app.util.vectordb import Pinecone, Row, RowType
from ulid import ulid

ner = NER()

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

    timestamp = int(time())
    graph_db = GraphDB(uri=graph_db_uri, user=secrets.get('GRAPH_DB_KEY'), password=secrets.get('GRAPH_DB_SECRET'))
    pinecone = Pinecone(api_key=secrets.get('PINECONE_API_KEY'), environment='us-east1-gcp')
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
    graph_db.close()
    
    if len(index_responses) > 0:
        db_update_items = []
        for response in index_responses:
            if response.succeeded:
                db_update_items.append(ParentChildItem(
                    parent=f'{KeyNamespaces.USER.value}{user}',
                    child=f'{KeyNamespaces.INTEGRATION.value}{response.integration}',
                ))
        db.update(db_update_items, timestamp=timestamp, last_fetch_timestamp=timestamp)

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
            documents: List[Document] = []
            entities: List[Entity] = []
            if not (discovery_response and discovery_response.items):
                return False
            next_token = discovery_response.next_token
            for item in discovery_response.items:
                fetch_response: FetchResponse = fetcher.fetch(item.id)
                nlp_response: NlpResponse = parse_chunks(api_key=openai_api_key, id=item.id, fetch_response=fetch_response) 
                if not nlp_response:
                    continue
                documents.append(nlp_response.document)
                entities.extend(nlp_response.entities)
                break
            
            rows: List[Row] = []
            for document in documents:
                rows.extend([Row(
                    id=relationship.target.id,
                    embedding=relationship.target.embedding,
                    owner=user,
                    document_id=document.id,
                    type=RowType.CHUNK
                ) for relationship in document.consists_of])
            
            for entity in entities:
                rows.extend([Row(
                    id=predicate.id,
                    embedding=predicate.embedding,
                    owner=user,
                    document_id=predicate.document,
                    type=RowType.TRIPLET
                ) for predicate in entity.predicates])
                
            pinecone_response = pinecone.upsert(rows)
            response = db.create_entities(entities=entities, documents=documents, owner=user, timestamp=timestamp)
            print(response)
            if not (pinecone_response and response):
                print('failed write response!')
                print(response)
                print(pinecone_response)
            if not next_token:
                break
    except Exception as e:
        print(e)
        print(fetcher._INTEGRATION)
        succeeded = False

    return IndexResponse(succeeded=succeeded, integration=fetcher._INTEGRATION, timestamp=timestamp)

@dataclass
class NlpResponse:
    document: Document
    entities: List[Entity]
    
MAX_CHILDREN = 10
def get_kg_chunks(api_key: str, chunks: List[str]) -> List[str]:
    if not (chunks and len(chunks) > 0):
        return []

    tree_chunks: List[Chunk] = []
    temp_chunks = chunks.copy()
    height = 0
    while len(temp_chunks) > 1:
        print('here!')
        temp_chunks_len = len(temp_chunks)
        join_chunks = []
        for chunk in temp_chunks:
            tree_chunks.append(Chunk(
                id=ulid(),
                embedding=get_embedding(api_key, chunk),
                content=chunk,
                height=height
            ))
        for i in range(0, temp_chunks_len, MAX_CHILDREN):
            join_chunks.append(summarize(api_key=api_key, text='\n\n'.join(temp_chunks[i:min(i+MAX_CHILDREN, temp_chunks_len)])))
        temp_chunks = join_chunks
        height += 1
    if len(temp_chunks) == 1:
        tree_chunks.append(Chunk(
            id=ulid(),
            embedding=get_embedding(api_key, temp_chunks[0]),
            content=temp_chunks[0],
            height=height
        ))
    print(tree_chunks)
    return tree_chunks

def parse_chunks(api_key: str, id: str, fetch_response: FetchResponse) -> NlpResponse:
    if not fetch_response:
        return None
    
    entities_dict: dict[str, Entity] = {}
    chunks: List[Chunk] = get_kg_chunks(api_key=api_key, chunks=[chunk.content for chunk in fetch_response.chunks])
    for chunk in chunks:
        knowledge_triplets = get_knowledge_triplets(api_key=api_key, text=chunk.content)
        print(knowledge_triplets)
        for triplet in knowledge_triplets:
            object_entity = Entity(
                id=triplet.object,
                type='llm',
            )
            predicate = PREDICATES(
                id=ulid(),
                embedding=get_embedding(api_key=api_key, text=f'{triplet.subject} {triplet.predicate} {triplet.object}'),
                text=triplet.predicate,
                chunk=chunk.id,
                document=id, 
                target=object_entity
            )
            if triplet.subject not in entities_dict:
                entities_dict[triplet.subject] = Entity(
                    id=triplet.subject,
                    type='llm',
                    predicates=[predicate]
                )
            else:
                entities_dict[triplet.subject].predicates.append(predicate)
        print(entities_dict)
    document = Document(
        id=id,
        integration=fetch_response.integration,
        consists_of=[CONSISTS_OF(target=chunk) for chunk in chunks]
    )
    print(document)
    return NlpResponse(document=document, entities=entities_dict.values())