import base64
from typing import Generator, List

import requests
from app.fetcher.base import (Block, BodyBlock, DiscoveryResponse, Fetcher,
                              Filter, Item, TitleBlock)


class GoogleMail(Fetcher):
    _INTEGRATION = 'google_mail'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://oauth2.googleapis.com/token',
            'refresh_endpoint': 'https://oauth2.googleapis.com/token',
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('google_mail discovery!')

        filters = {}
        if filter:
            if filter.next_token:
                filters['pageToken'] = filter.next_token
            if filter.limit:
                filters['maxResults'] = filter.limit

        succeeded = self.auth.refresh()
        if not succeeded:
            print('failed to refresh google mail token')
            return None
        
        response = requests.get(
            'https://www.googleapis.com/gmail/v1/users/me/threads',
            params={ **filters },
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        discovery_response = response.json() if response else None

        if not discovery_response:
            return None
        
        next_token = discovery_response.get('nextPageToken', None) if discovery_response else None
        threads = discovery_response.get('threads', None) if discovery_response else None

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon=self.get_icon(),
            items=[Item(
                id=thread.get('id', None) if thread else None,
                title=thread.get('snippet', None) if thread else None,
                link=f'https://mail.google.com/mail/u//#inbox/{thread["id"]}' if thread else None,
                preview=None
            ) for thread in threads],
            next_token=next_token
        )

    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('google_mail load!')
        self.auth.refresh()
        response = requests.get(
            f'https://www.googleapis.com/gmail/v1/users/me/threads/{id}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )

        load_response = response.json() if response else None
        messages = load_response.get('messages', None) if load_response else None
        message_parts = [message.get('payload', None) if messages else None for message in messages]
        if not message_parts or len(message_parts) == 0:
            return
        
        subjects = set()
        for part in message_parts:
            headers = part.get('headers', []) if part else []
            for subject in [header.get('value', None) for header in headers if header.get('name', None) == 'Subject']:
                if subject:
                    subjects.add(subject)
        for subject in subjects:
            yield TitleBlock(title=subject)
           
        texts: List[str] = []
        while len(message_parts) > 0:
            part = message_parts.pop(0)
            if not part:
                continue

            body = part.get('body', None)
            data = body.get('data', None) if body else None
            text = base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4)) if data else None
            text = text.decode('utf-8') if text else None
            if text:
                mime_type = part.get('mimeType', None) if part else None
                if mime_type and mime_type.startswith('text/plain'):
                    texts.append(text)

            parts = part.get('parts', None)
            if parts:
                message_parts[0:0] = parts

        for text in self._merge_split_texts(texts):
            yield BodyBlock(body=text)
