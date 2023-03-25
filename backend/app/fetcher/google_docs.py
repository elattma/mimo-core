from datetime import datetime
from typing import Generator, List

import requests
from app.fetcher.base import (Block, BodyBlock, DiscoveryResponse, Fetcher,
                              Filter, Item, TitleBlock)


class GoogleDocs(Fetcher):
    _INTEGRATION = 'google_docs'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://oauth2.googleapis.com/token',
            'refresh_endpoint': 'https://oauth2.googleapis.com/token',
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('google_docs discovery!')
        succeeded = self.auth.refresh() # TODO: handle refresh as a failure case and refresh db and abstract into base
        if not succeeded:
            print('failed to refresh google docs token')
            return None
        discover_filters = ['mimeType="application/vnd.google-apps.document"', 'trashed=false']
        if self.last_fetch_timestamp:
            date = datetime.fromtimestamp(self.last_fetch_timestamp)
            formatted_time = date.strftime('%Y-%m-%dT%H:%M:%S')
            discover_filters.append(f'(modifiedTime > "{formatted_time}" or sharedWithMeTime > "{formatted_time}")')
        params = {
            'q': ' and '.join(discover_filters)
        }
        if filter:
            if filter.next_token:
                params.update({
                    'pageToken': filter.next_token,
                })
        response = requests.get(
            'https://www.googleapis.com/drive/v3/files',
            params=params,
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        discovery_response = response.json()

        if not response or not discovery_response:
            print('failed to get google docs')
            return None
        
        next_token = discovery_response.get('nextPageToken', None)
        files = discovery_response.get('files', None)
        items = [Item(
            id=file.get('id', None) if file else None,
            title=file.get('name', None) if file else None,
            link=f'https://docs.google.com/document/d/{file.get("id", None)}' if file else None,
            preview=file.get('thumbnailLink', None)) if file else None
        for file in files] if files else []

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon=self.get_icon(),
            items=items,
            next_token=next_token
        )

    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('google_docs load!')
        self.auth.refresh()
        response = requests.get(
            f'https://docs.googleapis.com/v1/documents/{id}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        load_response = response.json() if response else None
        title = load_response.get('title', None) if load_response else None
        if title:
            yield TitleBlock(title=title)
        body = load_response.get('body', None) if load_response else None
        content = body.get('content', None) if body else None
        if not content:
            return
        
        texts: List[str] = []
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
                    texts.append(text)
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
            
        for text in self._merge_split_texts(texts):
            yield BodyBlock(body=text)