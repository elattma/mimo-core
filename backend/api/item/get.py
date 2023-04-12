import json
import os
from typing import List

from aws.response import Errors, to_response_error, to_response_success
from aws.secrets import Secrets
from fetcher.base import Item
from graph.blocks import BlockStream, TitleBlock
from graph.neo4j_ import Document, Neo4j

secrets: Secrets = None
neo4j: Neo4j = None

def handler(event: dict, context):
    global secrets, neo4j

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']
    graph_db_uri: str = os.environ["GRAPH_DB_URI"]

    if not (user and stage and upload_item_bucket):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)

    print(graph_db_uri)
    print(secrets.get("GRAPH_DB_KEY"))
    print(secrets.get("GRAPH_DB_SECRET"))
    if not neo4j:
        neo4j = Neo4j(
            uri=graph_db_uri,
            user=secrets.get("GRAPH_DB_KEY"),
            password=secrets.get("GRAPH_DB_SECRET"),
        )
    documents: List[Document] = neo4j.discover(user)
    response_items: List[Item] = []
    for document in documents:
        title = 'Untitled'
        if document.consists:
            try:
                block = document.consists[0].target
                title_dict = json.loads(block.content)
                title_stream = BlockStream.from_dict(block.label, title_dict)
                if title_stream.blocks:
                    title_block: TitleBlock = title_stream.blocks[0]
                    title = title_block.text
            except Exception as e:
                print('failed to cast title to a block stream!')
                print(block)
                print(e)
        item = Item(
            id=document.id,
            title=title,
            link=f'https://docs.google.com/document/d/{document.id}',
        )
        response_items.append(item)
            
    return to_response_success([response_item.__dict__ for response_item in response_items])