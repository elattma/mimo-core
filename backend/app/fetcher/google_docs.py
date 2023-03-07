from typing import Any, List

import requests
from app.fetcher.base import (Chunk, DiscoveryResponse, Fetcher, FetchResponse,
                              Filter)


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
        response = requests.get(
            'https://www.googleapis.com/drive/v3/files',
            params={
                'q': 'mimeType="application/vnd.google-apps.document" and trashed=false'
            },
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        discovery_response = response.json()

        if not response or not discovery_response:
            print('failed to get google docs')
            return None
        
        next_token = discovery_response.get('nextPageToken')
        files = discovery_response['files']

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon=self.get_icon(),
            items=[{
                'id': file['id'],
                'title': file['name'],
                'link': f'https://docs.google.com/document/d/{file["id"]}',
                'preview': file['thumbnailLink'] if 'thumbnailLink' in file else None
            } for file in files],
            next_token=next_token
        )

    def fetch(self, id: str) -> FetchResponse:
        print('google_docs load!')
        self.auth.refresh()
        response = requests.get(
            f'https://docs.googleapis.com/v1/documents/{id}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        load_response = response.json() if response else None
        print(load_response)
        body = load_response.get('body', None) if load_response else None
        content = body.get('content', None) if body else None
        print(content)
        if not content:
            print('failed to get doc')
            return None
        
        chunks: List[Chunk] = []
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
                    chunks.append(Chunk(content=text))
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

        return FetchResponse(
            integration=self._INTEGRATION,
            chunks=self.merge_split_chunks(chunks=chunks)
        )
