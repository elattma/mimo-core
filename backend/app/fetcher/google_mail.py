import base64
import re
from typing import List

import requests
from app.fetcher.base import (Chunk, DiscoveryResponse, Fetcher, FetchResponse,
                              Filter, Item)


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
            'https://www.googleapis.com/gmail/v1/users/me/messages',
            params={ **filters },
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )
        discovery_response = response.json()

        if not response or not discovery_response:
            print('failed to get google mail')
            return None
        
        next_token = discovery_response.get('nextPageToken', None) if discovery_response else None
        messages = discovery_response.get('messages', None) if discovery_response else None

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon=self.get_icon(),
            items=[Item(
                id=message.get('id', None) if message else None,
                title=message.get('snippet', None) if message else None,
                link=f'https://mail.google.com/mail/u//#inbox/{message["id"]}' if message else None,
                preview=None
            ) for message in messages],
            next_token=next_token
        )

    def fetch(self, id: str) -> FetchResponse:
        print('google_mail load!')
        self.auth.refresh()
        response = requests.get(
            f'https://www.googleapis.com/gmail/v1/users/me/messages/{id}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )

        load_response = response.json() if response else None
        message_part = load_response.get('payload', None) if load_response else None

        if not message_part:
            print('failed to get message')
            return None
        
        message_parts = [message_part]
        chunks: List[Chunk] = []
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
                    chunks.append(Chunk(content=text))

            parts = part.get('parts', None)
            if parts:
                message_parts[0:0] = parts

        # TODO: add fetching attachments

        return FetchResponse(
            integration=self._INTEGRATION,
            chunks=self.merge_split_chunks(chunks)
        )
    