from concurrent.futures import ThreadPoolExecutor, as_completed
from csv import writer
from dataclasses import dataclass
from io import StringIO
from typing import List

import boto3
from fetcher.model import StreamData


@dataclass
class FlushResult:
    succeeded: bool
    stream: StreamData

class S3Lake:
    _bucket_name: str
    _connection: str
    _batch_size: int

    _stream_data: List[StreamData]
    _failures: int

    def __init__(self, bucket_name: str, connection: str, batch_size: int = 100) -> None:
        self._s3_client = boto3.client('s3')
        self._bucket_name = bucket_name
        self._connection = connection
        self._batch_size = batch_size

        self._stream_data = []
        self._failures = 0

    def add(self, stream: StreamData):
        print('[add] name: ', stream._name, 'id: ', stream._id)
        self._stream_data.append(stream)
        if len(self._stream_data) >= self._batch_size:
            self.flush()

    def _flush(self, stream: StreamData) -> FlushResult:
        print('[_flush] name: ', stream._name, 'id: ', stream._id, 'into bucket: ', self._bucket_name, 'connection: ', self._connection)
        csv = StringIO()
        csv_writer = writer(csv)
        csv_writer.writerow(stream._data.keys())
        csv_writer.writerow(stream._data.values())
        response = self._s3_client.put_object(
            Bucket=self._bucket_name,
            Key=f'{self._connection}/{stream._name}/{stream._id}',
            Body=csv.getvalue(),
            ContentType='text/csv'
        )
        status_code = response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0)
        return FlushResult(
            succeeded=status_code == 200,
            stream=stream
        )

    def flush(self):
        print('[flush] bucket: ', self._bucket_name)
        if not self._stream_data:
            return

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self._flush, stream) for stream in self._stream_data]

        failed_streams = []
        for future in as_completed(futures):
            result = future.result()
            if not result.succeeded:
                print('[flush] failed to flush stream')
                failed_streams.append(result.stream)
                continue
            print(f'[flush] succeeded for {result.stream._id}!')

        if len(failed_streams) / len(self._stream_data) > 0.7:
            self._stream_data = failed_streams
            self._failures += 1        
        else:
            self._stream_data = []
            self._failures = 0
        
        if self._failures > 3:
            raise Exception('[flush] Too many failures')
        