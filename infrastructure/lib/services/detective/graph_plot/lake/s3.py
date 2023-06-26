from csv import DictReader
from typing import Dict, Generator, List

import boto3
from algos.classifier import Classifier


class S3Lake:
    _bucket_name: str
    _prefix: str
    _classifier = None
    _s3_client = None

    def __init__(self, bucket_name: str, prefix: str) -> None:
        if not self._s3_client:
            self._s3_client = boto3.client('s3')
        if not self._classifier:
            self._classifier = Classifier()
        self._bucket_name = bucket_name
        self._prefix = prefix

    def get_tables(self) -> List[str]:
        print(f'[S3Lake.get_tables] bucket_name: {self._bucket_name}, prefix: {self._prefix}')
        response = self._s3_client.list_objects_v2(
            Bucket=self._bucket_name,
            Prefix=self._prefix,
            Delimiter='/'
        )

        listed_tables = [common_prefix['Prefix'].split('/')[-2] for common_prefix in response.get('CommonPrefixes', [])]
        print(f'[S3Lake.get_tables] listed_tables: {listed_tables}')
        for table in listed_tables:
            self._classifier.get_normalized_label(table)

        return listed_tables
        
    def block_iterator(self, table: str) -> Generator[str, None, None]:
        print(f'[S3Lake.block_iterator] bucket_name: {self._bucket_name}, prefix: {self._prefix}, table: {table}')
        next_token = None
        while True:
            extra_args = {
                'ContinuationToken': next_token,
            } if next_token else {}

            response = self._s3_client.list_objects_v2(
                Bucket=self._bucket_name,
                Prefix=f'{self._prefix}{table}/',
                **extra_args
            )
            print(f'[S3Lake.block_iterator] response: {response}')
            next_token = response.get('NextContinuationToken', None)
            for content in response.get('Contents', []):
                yield content['Key']

            if not next_token:
                break

    def _get_block(self, block_key: str) -> str:
        print(f'[S3Lake._get_block] bucket_name: {self._bucket_name}, block_key: {block_key}')
        response = self._s3_client.get_object(
            Bucket=self._bucket_name,
            Key=block_key
        )
        return response['Body'].read().decode('utf-8')  
    
    def get_block_csv(self, block_key: str) -> List[Dict]:
        print(f'[S3Lake.get_block_csv] bucket_name: {self._bucket_name}, block_key: {block_key}')
        content = self._get_block(block_key)
        dict_list = []

        csv_reader = DictReader(content.splitlines())
        for row in csv_reader:
            dict_list.append(row)
        return dict_list
