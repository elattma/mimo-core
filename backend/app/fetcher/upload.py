import tempfile
from typing import List

import boto3
import nltk
from app.fetcher.base import (DiscoveryResponse, Fetcher, FetchResponse,
                              Filter, Item)

nltk.data.path.append('./nltk_data/')
from unstructured.partition.auto import partition


# TODO: add explicit error handling
class Upload(Fetcher):
    _INTEGRATION = 'upload'
    s3_client = None

    def __init__(self) -> None:
        super().__init__()
        if not self.s3_client:
            self.s3_client = boto3.client('s3')

    def get_auth_type(self) -> str:
        return 's3'
    
    def get_auth_attributes(self) -> dict:
        return {}

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        list_params = {
            'Bucket': self.auth.bucket,
            'Prefix': self.auth.prefix,
            'MaxKeys': 20,
        }

        if filter:
            if filter.next_token:
                list_params['ContinuationToken'] = filter.next_token
            if filter.limit:
                list_params['MaxKeys'] = filter.limit

        response = self.s3_client.list_objects_v2(**list_params)
        files: List[dict] = response.get('Contents', []) if response else []
        if len(files) < 1:
            print('empty uploads!')
            return None
        
        next_token = response.get('NextContinuationToken', None)
        items = []
        for file in files:
            if file.get('Key', None) and not file.get('Key', '').endswith('/'):
                items.append(Item(
                    id=file.get('Key', None),
                    title=file.get('Key', '').replace(f'{self.auth.prefix}/', ''),
                    link='', #TODO: make the links clickable?
                    preview=None # TODO: add preview?
                ))

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon='', #TODO: add mimo icon or whatever file type icon
            items=items,
            next_token=next_token
        )

    def fetch(self, id: str) -> FetchResponse:
        with tempfile.NamedTemporaryFile(mode='w') as temporary_file:
            self.s3_client.download_fileobj(
                Bucket=self.auth.bucket,
                Key=id,
                Fileobj=temporary_file
            )
            temporary_file.seek(0)
            elements = partition(file=temporary_file)
            
        chunks = self.merge_split_chunks([str(element) for element in elements])

        return FetchResponse(
            integration=self._INTEGRATION,
            chunks=self.merge_split_chunks(chunks=chunks)
        )

    def generate_presigned_url(self, name: str, content_type: str, **kwargs) -> str:
        return self.s3_client.generate_presigned_url(
            ClientMethod='put_object', 
            Params={
                'Bucket': self.auth.bucket,
                'Key': f'{self.auth.prefix}/{name}',
                'ContentType': content_type,
                **kwargs
            },
        )
    