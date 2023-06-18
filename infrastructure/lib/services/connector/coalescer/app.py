import os
import sys
import traceback
from argparse import ArgumentParser
from typing import Dict

from auth.base import AuthStrategy, AuthType
from fetcher.base import Fetcher
from lake.s3 import S3Lake
from shared.model import Integration
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB
from state.params import SSM

_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--library', type=str, required=True)

def main():
    pc_table = os.getenv('PARENT_CHILD_TABLE')
    integrations_path = os.getenv('INTEGRATIONS_PATH')
    lake_bucket_name = os.getenv('LAKE_BUCKET_NAME')
    if not (pc_table and integrations_path and lake_bucket_name):
        raise Exception('missing env vars!')
    
    args = _arg_parser.parse_args()
    args = vars(args)
    connection = args.get('connection', None)
    library = args.get('library', None)
    if not (connection and library):
        raise Exception('[main] missing args!')

    db = ParentChildDB(table_name=pc_table)
    item: LibraryConnectionItem = db.get(
        f'{KeyNamespaces.LIBRARY.value}{library}',
        f'{KeyNamespaces.CONNECTION.value}{connection}'
    )
    integration_params = SSM().load_params(f'{integrations_path}/{item.connection.integration}')
    integration = Integration.from_dict(integration_params)

    auth_strategy = None
    if item.connection.auth:    
        auth_dict: Dict = item.connection.auth.as_dict()
        auth_type = auth_dict.pop('type')
        auth_type = AuthType(auth_type) if auth_type else None
        auth_strategy: AuthStrategy = integration.auth_strategies.get(auth_type)
        auth_strategy.auth(**auth_dict)

    fetcher: Fetcher = Fetcher.create(
        integration=integration.id,
        auth_strategy=auth_strategy, 
        config=item.connection.config,
        last_ingested_at=0, 
        limit=1
    )
    s3_lake = S3Lake(
        bucket_name=lake_bucket_name,
        connection=connection
    )

    for stream in fetcher.discover():
        fetcher.fetch(stream)
        s3_lake.add(stream)

    s3_lake.flush()
    
if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f'error: {str(e)}')
        print(traceback.format_exc())
        sys.exit(1)