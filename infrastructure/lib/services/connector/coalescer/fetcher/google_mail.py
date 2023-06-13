import base64
from typing import Dict, Generator, List

from auth.base import AuthType
from dstruct.model import Block, Discovery
from fetcher.base import Fetcher

DISCOVERY_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads'
GET_THREADS_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads/{id}'

class GoogleMail(Fetcher):
    _INTEGRATION = 'google_mail'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def discover(self) -> Generator[Discovery, None, None]:
        next_token = None
        params = {}
        while True:
            if next_token:
                params.update({
                    'pageToken': next_token
                })
            
            response = self.request(DISCOVERY_ENDPOINT, params=params)
            next_token = response.get('nextPageToken', None) if response else None
            threads: List[Dict] = response.get('threads', None) if response else None

            for thread in threads:
                thread_id = thread.get('id', None) if thread else None
                yield Discovery(
                    id=thread_id,
                    type='thread'
                )

            if not next_token:
                break

    def _get_author(self, headers: Dict) -> str:
        for header in headers:
            if not header or 'name' not in header:
                continue
            if header.get('name') == 'From':
                return header.get('value')
    
    def _get_title(self, headers: Dict) -> str:
        for header in headers:
            if not header or 'name' not in header:
                continue
            if header.get('name') == 'Subject':
                return header.get('value')
    
    def _get_recipients(self, headers: Dict) -> List[str]:
        recipients = []
        for header in headers:
            if not header or 'name' not in header:
                continue
            if header.get('name') == 'To':
                recipients.append(header.get('value'))
        return recipients
    
    def _get_body(self, message: Dict) -> str:
        message_parts = [message.get('payload', None)] if message else None
        if not message_parts:
            return None

        body: List[str] = []
        while len(message_parts) > 0:
            part: Dict = message_parts.pop(0)
            if not part:
                continue

            body = part.get('body', None)
            data = body.get('data', None) if body else None
            text = base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4)) if data else None
            text = text.decode('utf-8') if text else None
            if text:
                mime_type = part.get('mimeType', None) if part else None
                if mime_type and mime_type.startswith('text/plain'):
                    body.append(text)

            parts = part.get('parts', None)
            if parts:
                message_parts[0:0] = parts
        
        return '\n'.join(body)

    def fetch_thread(self, discovery: Discovery) -> None:
        response = self.request(GET_THREADS_ENDPOINT.format(id=discovery.id))
        messages: List[Dict] = response.get('messages', None) if response else None
        if not messages:
            return

        thread_id = response.get('id', None) if response else None
        for message in messages:
            part = message.get('payload', None) if message else None
            headers = part.get('headers', []) if part else []
            last_updated_timestamp = message.get('internalDate', None) if message else None

            author = self._get_author(headers)
            title = self._get_title(headers)
            recipients = self._get_recipients(headers)
            body = self._get_body(part)
            block = Block(
                label='email',
                last_updated_timestamp=last_updated_timestamp,
                properties={
                    'author': author,
                    'title': title,
                    'recipients': recipients,
                    'body': body,
                    'thread_id': thread_id
                }
            )
            discovery.add_blocks([block])

    def fetch(self, discovery: Discovery) -> None:
        if discovery.type == 'thread':
            self.fetch_thread(discovery)
