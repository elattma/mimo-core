import base64
from typing import Dict, Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher, StreamData

DISCOVERY_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads'
GET_THREADS_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads/{id}'

class GoogleMail(Fetcher):
    _INTEGRATION = 'google_mail'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def discover(self) -> Generator[StreamData, None, None]:
        next_token = None
        params = {}
        limit = self._filter.limit if self._filter else None
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
                if not thread_id:
                    continue
                yield StreamData(
                    name='email_thread',
                    id=thread_id,
                )
                if limit:
                    limit -= 1
                    if limit < 1:
                        return []

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
    
    def _get_body(self, message_parts: List[Dict]) -> str:
        if not message_parts:
            return None

        body_list: List[str] = []
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
                    body_list.append(text)

            parts = part.get('parts', None)
            if parts:
                message_parts[0:0] = parts
        
        return '\n\n'.join(body_list)

    def fetch_thread(self, stream: StreamData) -> None:
        response = self.request(GET_THREADS_ENDPOINT.format(id=stream._id))
        messages: List[Dict] = response.get('messages', None) if response else None
        if not messages:
            return

        thread_id = response.get('id', None) if response else None
        for message in messages:
            payload = message.get('payload', None) if message else None
            headers = payload.get('headers', []) if payload else []
            last_updated_timestamp = message.get('internalDate', None) if message else None

            author = self._get_author(headers)
            title = self._get_title(headers)
            recipients = self._get_recipients(headers) 
            body = self._get_body(payload.get('parts', None) if payload else None)

            stream.add_structured_data_as_list('author', author)
            stream.add_unstructured_data('title', title)
            stream.add_structured_data_as_list('recipients', recipients)
            stream.add_unstructured_data('body', body)
        stream.add_structured_data('last_updated_timestamp', last_updated_timestamp)

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'email_thread':
            self.fetch_thread(stream)
