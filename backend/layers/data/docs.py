from typing import Any, List

import requests
from data.fetcher import Chunk, DiscoveryResponse, Fetcher, FetchResponse


class Docs(Fetcher):
    def discover(self, filter: Any = None) -> DiscoveryResponse:
        print('google discovery!')
        response = requests.get(
            'https://www.googleapis.com/drive/v3/files',
            params={
                'q': 'mimeType="application/vnd.google-apps.document" and trashed=false'
            },
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        print(response)
        discovery_response = response.json()
        print(discovery_response)

        if not response or not discovery_response:
            print('failed to get google docs')
            return None
        
        next_token = discovery_response.get('nextPageToken')
        files = discovery_response['files']

        return DiscoveryResponse(
            integration='google', 
            icon='https://www.gstatic.com/images/branding/product/1x/drive_512dp.png', 
            items=[{
                'id': file['id'],
                'title': file['name'],
                'link': f'https://docs.google.com/document/d/{file["id"]}',
                'preview': file['thumbnailLink'] if 'thumbnailLink' in file else None
            } for file in files],
            next_token=next_token
        )

    def fetch(self, id: str) -> FetchResponse:
        print('google load!')
        response = requests.get(
            f'https://docs.googleapis.com/v1/documents/{id}',
            headers={
                'Authorization': f'Bearer {self.access_token}'
            }
        )
        print(response)
        load_response = response.json()
        print(load_response)

        if not response or not load_response or 'body' not in load_response or 'content' not in load_response['body']:
            print('failed to get doc')
            return None
        
        content: List[Any] = load_response['body']['content']
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
            integration='google',
            icon='https://www.gstatic.com/images/branding/product/1x/drive_512dp.png',
            chunks=self.merge_split_chunks(chunks=chunks)
        )
