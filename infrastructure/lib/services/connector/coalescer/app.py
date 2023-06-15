import os
from argparse import ArgumentParser
from typing import Dict

from auth.base import AuthStrategy, AuthType
from dstruct.ingestor import Ingestor
from dstruct.neo4j_ import Neo4j
from dstruct.pinecone_ import Pinecone
from fetcher.base import Fetcher
from shared.model import Integration
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB
from state.params import SSM
from util.model import CoalescerArgs
from util.openai_ import OpenAI
from util.translator import Translator

_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--library', type=str, required=True)

def main():
    pc_table = os.getenv('PARENT_CHILD_TABLE')
    integrations_path = os.getenv('INTEGRATIONS_PATH')
    app_secrets_path = os.getenv('APP_SECRETS_PATH')
    if not (pc_table and integrations_path and app_secrets_path):
        raise Exception('missing env vars!')
    
    args = _arg_parser.parse_args()
    coalescer_args = CoalescerArgs(**vars(args))

    if not coalescer_args.valid():
        raise Exception('invalid coalescer args!')
    
    app_secrets = SSM().load_params(app_secrets_path)
    if not app_secrets:
        raise Exception('empty app secrets!')

    openai_api_key = app_secrets.get('openai_api_key', None)
    neo4j_user = app_secrets.get('neo4j_user', None)
    neo4j_password = app_secrets.get('neo4j_password', None)
    pinecone_api_key = app_secrets.get('pinecone_api_key', None)
    if not (openai_api_key and neo4j_user and neo4j_password and pinecone_api_key):
        raise Exception('missing app secrets!')

    db = ParentChildDB(table_name=pc_table)
    item: LibraryConnectionItem = db.get(
        f'{KeyNamespaces.LIBRARY.value}{coalescer_args.library}',
        f'{KeyNamespaces.CONNECTION.value}{coalescer_args.connection}'
    )
    integration_params = SSM().load_params(f'{integrations_path}/{item.connection.integration}')
    integration = Integration.from_dict(integration_params)

    auth_dict: Dict = item.connection.auth.as_dict()
    auth_type = auth_dict.pop('type')
    auth_type = AuthType(auth_type) if auth_type else None
    auth_strategy: AuthStrategy = integration.auth_strategies.get(auth_type)
    auth_strategy.auth(**auth_dict)
    fetcher: Fetcher = Fetcher.create(integration.id, auth_strategy, 0, 100)
    ingestor = Ingestor(
        openai=OpenAI(openai_api_key),
        translator=Translator(),
        neo4j=Neo4j(
            uri='neo4j+s://67eff9a1.databases.neo4j.io',
            user=neo4j_user,
            password=neo4j_password
        ),
        pinecone=Pinecone(
            library=coalescer_args.library,
            api_key=pinecone_api_key,
            environment='us-east1-gcp'
        ),
        library=coalescer_args.library,
        connection=item.connection.id
    )

    succeeded = True
    for discovery in fetcher.discover():
        try:
            fetcher.fetch(discovery)
            succeeded = ingestor.add(discovery)
            if not succeeded:
                succeeded = False
                break
        except Exception as e:
            succeeded = False
            print(f'error: {str(e)}')
            break
    
    ingestor.close()
    print(str(ingestor._stats.as_dict()))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f'error: {str(e)}')
        