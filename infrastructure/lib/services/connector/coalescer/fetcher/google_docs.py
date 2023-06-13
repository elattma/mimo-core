from typing import Dict, Generator, List

from auth.base import AuthType
from dstruct.model import Block, Discovery

from .base import Fetcher, get_timestamp_from_format

GOOGLE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DISCOVERY_ENDPOINT = 'https://www.googleapis.com/drive/v3/files'
GET_METADATA_ENDPOINT = 'https://www.googleapis.com/drive/v3/files/{id}'
GET_DOCUMENT_ENDPOINT = 'https://docs.googleapis.com/v1/documents/{id}'


class GoogleDocs(Fetcher):
    _INTEGRATION = 'google_docs'

    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.BASIC, AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT]
    
    def discover(self) -> Generator[Discovery, None, None]:
        discover_filters = ['mimeType="application/vnd.google-apps.document"', 'trashed=false']
        params = {
            'q': ' and '.join(discover_filters)
        }
        next_token = None
        while True:
            if next_token:
                params.update({
                    'pageToken': next_token
                })
            
            response = self.request(DISCOVERY_ENDPOINT, params=params)
            next_token = response.get('nextPageToken', None) if response else None
            files: List[Dict] = response.get('files', None) if response else None
            for file in files:
                file_id = file.get('id', None) if file else None
                yield Discovery(
                    id=file_id,
                    type='document'
                )

            if not next_token:
                break
    
    def _get_owners(self, owners_dict: Dict) -> List[str]:
        owners: List[str] = []
        for owner in owners_dict:
            if not owner or 'emailAddress' not in owner:
                continue
            owners.append(owner.get('emailAddress'))
        return owners

    def _get_body(self, body_dict: Dict) -> str:
        content = body_dict.get('content', None) if body_dict else None
        if not content:
            return
        
        body: List[str] = []
        while content and len(content) > 0:
            value = content.pop(0)
            if not value:
                continue
            if 'paragraph' in value and 'elements' in value['paragraph']:
                text: str = ""
                for element in value['paragraph']['elements']:
                    text += element['textRun']['content'] if 'textRun' in element else ''
                text = text.strip().replace('\n', '')
                if len(text) > 0:
                    body.append(text)
            elif 'table' in value and 'tableRows' in value['table']:
                for table_row in value['table']['tableRows']:
                    if not table_row or 'tableCells' not in table_row:
                        continue
                    for cell in table_row['tableCells']:
                        if not cell or 'content' not in cell:
                            continue
                        content[0:0] = cell['content']
            elif 'tableOfContents' in value and 'content' in value['tableOfContents']:
                content[0:0] = value['tableOfContents']['content']
        
        return '\n\n'.join(body)

    def _get_last_updated_timestamp(self, modifiedTime: str) -> int:
        return get_timestamp_from_format(modifiedTime, GOOGLE_TIME_FORMAT)

    def fetch_document(self, discovery: Discovery) -> None:
        response = self.request(
            GET_METADATA_ENDPOINT.format(id=discovery.id),
            params={
                'fields': 'modifiedTime, owners'
            }
        )
        last_updated_timestamp = self._get_last_updated_timestamp(response.get('modifiedTime', None)) if response else None
        owners = self._get_owners(response.get('owners', None) if response else None)

        response = self.request(GET_DOCUMENT_ENDPOINT.format(id=discovery.id))
        title = response.get('title', None)
        body = self._get_body(response.get('body', None))
        discovery.add_blocks([Block(
            last_updated_timestamp=last_updated_timestamp,
            label='document',
            properties={
                'title': title,
                'body': body,
                'owners': owners
            }
        )])

    def fetch(self, discovery: Discovery) -> None:
        if discovery.type == 'document':
            self.fetch_document(discovery)
