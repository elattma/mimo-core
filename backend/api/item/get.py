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

integration_to_link = {
    'google_docs': 'https://docs.google.com/document/d/{id}',
    'google_mail': 'https://mail.google.com/mail/u//#inbox/{id}',
    'slack_messaging': 'https://slack.com/channels/{id}',
    'notion': 'https://www.notion.so/{id}'
}

def handler(event: dict, context):
    global secrets, neo4j

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    graph_db_uri: str = os.environ["GRAPH_DB_URI"]

    if not (user and stage):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not secrets:
        secrets = Secrets(stage)

    if not neo4j:
        neo4j = Neo4j(
            uri=graph_db_uri,
            user=secrets.get("GRAPH_DB_KEY"),
            password=secrets.get("GRAPH_DB_SECRET"),
        )
    documents: List[Document] = neo4j.discover('google-oauth2|108573573074253667565')
    items_list = []
    for document in documents:
        title = None
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
        if not title:
            continue

        link = integration_to_link.get(document.integration, None)
        link = link.format(id=document.id) if link else None
        icon = f'assets.mimo.team/icons/{document.integration}.svg'
        item = Item(
            integration=document.integration,
            id=document.id,
            title=title,
            icon=icon,
            link=link,
        )
        items_list.append(item)

    return to_response_success({
        'items': [item.__dict__ for item in items_list],
        'next_token': None,
    })