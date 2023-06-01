import os
from argparse import ArgumentParser
from datetime import datetime
from typing import Generator

from fetcher.base import Fetcher
from lake.model import Drop
from lake.s3 import S3Lake
from util.model import Batch, Batcher, TundraArgs


def fetch(fetcher: Fetcher) -> Generator[Batch, None, None]:
    batcher = Batcher()
    for discovery in fetcher.discover():
        sections = fetcher.fetch(discovery)
        for batch in batcher.add(sections):
            yield batch
    
    yield from batcher.flush()

_lake: S3Lake = None
_arg_parser: ArgumentParser = ArgumentParser()
_arg_parser.add_argument('--user', type=str, required=True)
_arg_parser.add_argument('--connection', type=str, required=True)
_arg_parser.add_argument('--integration', type=str, required=True)
_arg_parser.add_argument('--access_token', type=str, required=True)
_arg_parser.add_argument('--limit', type=str, default="100")

def main():
    global _lake
    
    args = _arg_parser.parse_args()
    tundra_args = TundraArgs(**vars(args))
    bucket = os.getenv('DATA_LAKE')
    if not tundra_args.valid():
        print('invalid tundra args!')
        return

    if not _lake:
        _lake = S3Lake(
            owner=tundra_args.user,
            bucket_name=bucket
        )

    fetcher: Fetcher = Fetcher.create(
        tundra_args.integration, 
        tundra_args.access_token, 
        int(0), 
        int(tundra_args.limit)
    )
    
    now = datetime.now()
    for batch in fetch(fetcher):
        print(f'batch: {batch}')
        drop = Drop(
            batch=batch,
            name=f'{tundra_args.integration}_{tundra_args.connection}',
            datetime=now,
        )
        try:
            _lake.pour(drop)
        except Exception as e:
            print('something went wrong with pouring to our lake!', e)
            # checkpoint
    try:
        _lake.flush()
    except Exception as e:
        print('something went wrong with flushing our lake!', e)
        # checkpoint

if __name__ == '__main__':
    main()