from typing import List

from data.fetcher import DiscoveryResponse, Fetcher, FetchResponse
from data.filter import FetcherFilter
from mypy_boto3_s3 import S3Client


# TODO: add explicit error handling
class Upload(Fetcher):
    def __init__(self, access_token: str, s3_client: S3Client, bucket: str, prefix: str) -> None:
        super().__init__(access_token=access_token)
        self.s3_client = s3_client
        self.bucket = bucket
        self.prefix = prefix

    def discover(self, filter: FetcherFilter = None) -> DiscoveryResponse:
        list_params = {
            'Bucket': self.bucket,
            'Prefix': self.prefix,
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
        
        next_token = response.get('NextContinuationToken')
        return DiscoveryResponse(
            integration='upload', 
            icon='', #TODO: add mimo icon or whatever file type icon
            items=[{
                'id': file.get('Key', None),
                'title': file.get('Key', '').replace(self.prefix, ''),
                'link': '', #TODO: make the links clickable?
                'preview': None # TODO: add preview?
            } for file in files],
            next_token=next_token
        )

    def fetch(self, id: str) -> FetchResponse:
        return FetchResponse(
        )
