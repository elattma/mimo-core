from datetime import datetime
from typing import Dict, Generator, List
from uuid import uuid5

from base import Fetcher
from model import Page, PageType, Section, UnstructuredTextSection
from util import generate, get_timestamp_from_format

GOOGLE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'
DISCOVERY_ENDPOINT = 'https://www.googleapis.com/drive/v3/files'
GET_METADATA_ENDPOINT = 'https://www.googleapis.com/drive/v3/files/{id}'
GET_DOCUMENT_ENDPOINT = 'https://docs.googleapis.com/v1/documents/{id}'

class GoogleDocs(Fetcher):
    _INTEGRATION = 'google_docs'

    def discover(self) -> Generator[PageType, None, None]:
        max_pages = self._filter.limit if self._filter and self._filter.limit else None
        discover_filters = ['mimeType="application/vnd.google-apps.document"', 'trashed=false']
        if self._filter:
            if self._filter.start_timestamp:
                date = datetime.fromtimestamp(self._filter.start_timestamp)
                formatted_time = date.strftime('%Y-%m-%dT%H:%M:%S')
                discover_filters.append(f'(modifiedTime > "{formatted_time}" or sharedWithMeTime > "{formatted_time}")')
            if self._filter.limit:
                discover_filters.append(f'limit {self._filter.limit}')
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
            discovery_response: Dict = response.json() if response else None
            next_token = discovery_response.get('nextPageToken', None) if discovery_response else None
            files: List[Dict] = discovery_response.get('files', None) if discovery_response else None
            for file in files:
                file_id = file.get('id', None) if file else None
                yield Page(
                    id=file_id,
                    type=PageType.DOCS
                )
                max_pages -= 1
                if max_pages < 1:
                    return
    
    def _generate_member(self, response: Dict, lut: int) -> Generator[BlockStream, None, None]:
        owners: List[dict] = response.get('owners', None)
        member_blocks: List[MemberBlock] = []
        for owner in owners:
            if not owner or 'emailAddress' not in owner:
                continue
            name_entity = entity(id=owner.get('emailAddress', None),value=owner.get('displayName', None))
            member_blocks.append(MemberBlock(last_updated_timestamp=lut, name=name_entity, relation=Relations.AUTHOR))

        yield from generate(MemberBlock._LABEL, member_blocks)

    def _generate_title(self, response: Dict, lut: int) -> Generator[BlockStream, None, None]:
        title = response.get('title', None)
        uuid5()
        if title:
            yield UnstructuredTextSection(
                id=
                TitleBlock._LABEL, [TitleBlock(text=title, last_updated_timestamp=lut)])

    def _generate_body(self, response: Dict, lut: int) -> Generator[BlockStream, None, None]:
        body = response.get('body', None)
        content = body.get('content', None) if body else None
        if not content:
            return
        
        body_blocks: List[BodyBlock] = []
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
                    body_blocks.append(BodyBlock(text=text, last_updated_timestamp=lut))
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
        
        yield from generate(BodyBlock._LABEL, body_blocks)

    def _get_lut(self, response: dict) -> int:
        return get_timestamp_from_format(response.get('modifiedTime', None), GOOGLE_TIME_FORMAT) if response else None

    def fetch(self, page: Page) -> Generator[Section, None, None]:
        print('google_docs load!')
        response = self._request_session.get(
            GET_METADATA_ENDPOINT.format(id=page.id),
            params={
                'fields': 'modifiedTime, owners'
            }
        )
        metadata_response: dict = response.json() if response else None
        lut = None
        if metadata_response:
            lut = self._get_lut(metadata_response)
            yield from self._generate_member(metadata_response, lut)

        response = self._request_session.get(GET_DOCUMENT_ENDPOINT.format(id=page.id))
        load_response: dict = response.json() if response else None
        yield from self._generate_title(load_response, lut)

        yield from self._generate_body(load_response, lut)