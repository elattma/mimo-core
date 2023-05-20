from datetime import datetime
from typing import Generator

from fetcher.base import Fetcher
from lake.model import Drop
from lake.s3 import S3Lake
from util.model import Batch, Batcher


def fetch(fetcher: Fetcher) -> Generator[Batch, None, None]:
    batcher = Batcher()
    for discovery in fetcher.discover():
        sections = fetcher.fetch(discovery)
        for batch in batcher.add(sections):
            yield batch
    
    yield from batcher.flush()

_lake: S3Lake = None

def main():
    global _lake

    user: str = None
    connection: str = None
    integration: str = None
    access_token: str = None
    last_ingested_at: int = None
    limit: int = 100

    if not _lake:
        _lake = S3Lake()

    fetcher: Fetcher = Fetcher.create(integration, access_token, last_ingested_at, limit)
    
    date = datetime.now()
    for batch in fetch(fetcher):
        print(f'batch: {batch}')
        drop = Drop(
            name=f'{integration}_{connection}',
            type=batch._section_type,
            date=date,
        )
        try:
            _lake.pour(drop)
        except Exception as e:
            print('something went wrong with pouring to our lake!', e)
            # checkpoint

print('here! hello world!')
