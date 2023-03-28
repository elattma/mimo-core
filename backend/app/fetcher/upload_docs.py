import tempfile
from typing import Generator, List

import boto3
import nltk
from app.model.blocks import BlockStream, BodyBlock, TitleBlock

nltk.data.path.append('./nltk_data/')
from app.fetcher.base import DiscoveryResponse, Fetcher, Filter, Item


# TODO: add explicit error handling
# TODO: only docs, no other file types yet supported. Need to add in other classes
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
        print(response)
        
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

    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        from unstructured.partition.auto import partition

        with tempfile.NamedTemporaryFile() as temporary_file:
            self.s3_client.download_fileobj(
                Bucket=self.auth.bucket,
                Key=id,
                Fileobj=temporary_file,
            )
            temporary_file.seek(0)
            elements = partition(file=temporary_file)
        
        body_blocks: List[BodyBlock] = [BodyBlock(body=str(element)) for element in elements]

        yield BlockStream(TitleBlock._LABEL, [TitleBlock(title=id.replace(f'{self.auth.prefix}/', ''))])

        for body_stream in self._streamify_blocks(BodyBlock._LABEL, body_blocks):
            yield body_stream

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
    