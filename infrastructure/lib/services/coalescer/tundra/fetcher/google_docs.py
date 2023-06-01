from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Generator, List, Tuple

from .base import Discovery, Fetcher, Section, get_timestamp_from_format

GOOGLE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DISCOVERY_ENDPOINT = 'https://www.googleapis.com/drive/v3/files'
GET_METADATA_ENDPOINT = 'https://www.googleapis.com/drive/v3/files/{id}'
GET_DOCUMENT_ENDPOINT = 'https://docs.googleapis.com/v1/documents/{id}'

@dataclass
class DocumentSection(Section):
    title: str = None
    body: str = None
    owners: List[Tuple] = None
    last_updated_timestamp: int = None

    @classmethod
    def headers(cls) -> List[str]:
        return ['id', 'title', 'body', 'owners', 'last_updated_timestamp']

    def row(self) -> List[Any]:
        return [self.discovery.id, self.title, self.body, self.owners, self.last_updated_timestamp]

class GoogleDocs(Fetcher):
    _INTEGRATION = 'google_docs'

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
            
            response = self._request_session.get(DISCOVERY_ENDPOINT, params=params)
            print(str(response))
            discovery_response: Dict = response.json() if response else None
            print(discovery_response)
            next_token = discovery_response.get('nextPageToken', None) if discovery_response else None
            files: List[Dict] = discovery_response.get('files', None) if discovery_response else None
            for file in files:
                file_id = file.get('id', None) if file else None
                yield Discovery(
                    id=file_id,
                    type='document'
                )

            if not next_token:
                break
    
    def _get_owners(self, owners_dict: Dict) -> List[Tuple]:
        owners: List[Tuple] = []
        for owner in owners_dict:
            if not owner or 'emailAddress' not in owner:
                continue
            owners.append((owner.get('emailAddress'), owner.get('displayName', None)))

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

    def _get_lut(self, modifiedTime: str) -> int:
        return get_timestamp_from_format(modifiedTime, GOOGLE_TIME_FORMAT)

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('google_docs load!')
        response = self._request_session.get(
            GET_METADATA_ENDPOINT.format(id=discovery.id),
            params={
                'fields': 'modifiedTime, owners'
            }
        )
        metadata_response: dict = response.json() if response else None
        lut = self._get_lut(metadata_response.get('modifiedTime', None)) if metadata_response else None
        owners = self._get_owners(metadata_response.get('owners', None) if metadata_response else None)

        response = self._request_session.get(GET_DOCUMENT_ENDPOINT.format(id=discovery.id))
        load_response: dict = response.json() if response else None
        title = load_response.get('title', None)
        body = self._get_body(load_response.get('body', None))
        document = DocumentSection(
            discovery=discovery,
            last_updated_timestamp=lut,
            title=title,
            body=body,
            owners=owners,
        )
        return [document]