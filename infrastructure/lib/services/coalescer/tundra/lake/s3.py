from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import boto3

from .model import Drop, PourResult


class S3Lake:
    _owner: str
    _drops: List[Drop]
    _bucket_name: str
    _batch_size: int
    _failures: int

    def __init__(self, owner: str, bucket_name: str, batch_size: int = 100):
        self._s3_client = boto3.client('s3')
        self._owner = owner
        self._drops = []
        self._bucket_name = bucket_name
        self._batch_size = batch_size
        self._failures = 0

    def pour(self, drop: Drop):
        print(f'adding {drop}!')
        self._drops.append(drop)
        if len(self._drops) >= self._batch_size:
            self.flush()

    def _pour(self, drop: Drop) -> PourResult:
        print(f'pouring {drop} into {self._bucket_name}!')
        response = self._s3_client.put_object(
            Bucket=self._bucket_name,
            Key=f'{self._owner}/{drop.key()}',
            Body=drop._batch.csv(),
        )
        status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
        succeeded = status_code == 200
        return PourResult(
            succeeded=succeeded,
            drop=drop,
            error=status_code if not succeeded else None,
        )

    def flush(self):
        print(f'flushing {self._bucket_name}!')
        if not self._drops:
            return True
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._pour, drop) for drop in self._drops]

        failed_drops = []
        for future in as_completed(futures):
            result: PourResult = future.result()
            if not result.succeeded:
                print(f'failed to pour {result.drop._id} into {self._bucket_name}: {result.error}')
                failed_drops.append(result.drop)
                continue
            print(f'pour succeeded for {result.drop._id}!')
        
        if len(failed_drops) / len(self._drops) > 0.7:
            self._drops = failed_drops
            self._failures += 1
        else:
            self._drops = []
            self._failures = 0
        
        if self._failures > 3:
            raise Exception('too many failures')
        