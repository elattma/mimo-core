from typing import Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher
from fetcher.model import StreamData


class UploadFile(Fetcher):
    _INTEGRATION = 'upload_file'
    _s3_client = None
    
    def _get_supported_auth_types(sef) -> List[AuthType]:
        return []
    
    def discover(self) -> Generator[StreamData, None, None]:
        s3_bucket = self._config.get('s3_bucket', None) if self._config else None
        files = self._config.get('files', None) if self._config else None

        if not (s3_bucket and files):
            raise Exception(f'UploadFile.discover() invalid config.. {self._config}')

        if not self._s3_client:
            import boto3
            self._s3_client = boto3.client('s3')

        limit = self._filter.limit if self._filter else None
        for file in files:
            response = self._s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=file)
            if not response.get('Contents', []):
                raise Exception(f'UploadFile.discover() file not found.. {file}')
            yield StreamData(
                name='document',
                id=file,
            )
            if limit:
                limit -= 1
                if limit < 1:
                    return []
                
    def fetch_document(self, stream: StreamData) -> None:
        from tempfile import NamedTemporaryFile

        from unstructured.partition.auto import partition

        if not self._s3_client:
            import boto3
            self._s3_client = boto3.client('s3')

        s3_bucket = self._config.get('s3_bucket', None) if self._config else None
        key = stream._id if stream else None
        if not (s3_bucket and key):
            raise Exception(f'UploadFile.fetch() invalid config.. {self._config}')
        
        with NamedTemporaryFile() as temp_file:
            self._s3_client.download_fileobj(
                Bucket=s3_bucket,
                Key=key,
                Fileobj=temp_file
            )
            temp_file.seek(0)
            elements = partition(file=temp_file)

            for element in elements:
                stream.add_unstructured_data('body', str(element))
        stream._id = stream._id.split('/')[-1]
        stream._id = ''.join(stream._id.split('.')[0:-1])
        stream.add_unstructured_data('title', stream._id)

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'document':
            self.fetch_document(stream)
