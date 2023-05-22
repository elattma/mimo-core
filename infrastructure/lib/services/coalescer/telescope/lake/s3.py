from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import boto3
from mypy_boto3_s3 import S3Client


class S3Lake:
    _s3_client: S3Client
    _owner: str
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

   
