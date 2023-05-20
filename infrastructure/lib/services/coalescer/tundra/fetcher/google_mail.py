import base64
from dataclasses import dataclass
from typing import Dict, Generator, List, Set, Tuple

from base import Discovery, Fetcher, Section

DISCOVERY_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads'
FETCH_THREADS_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads/{id}'

@dataclass
class ThreadSection(Section):
    title: str = None
    body: str = None
    owners: List[Tuple] = None

    def row(self) -> str:
        return f'{self.discovery.id}, {self.title}, {self.body}, {self.owners}, {self.last_updated_timestamp}'

class GoogleMail(Fetcher):
    _INTEGRATION = 'google_mail'

    def discover(self) -> Generator[Discovery, None, None]:
        print('google_mail discovery!')

        filters = {}
        next_token = None
        while True:
            if next_token:
                filters.update({
                    'pageToken': next_token
                })
            
            response = self._request_session.get(DISCOVERY_ENDPOINT, params={ **filters })
            discovery_response: Dict = response.json() if response else None
            next_token = discovery_response.get('nextPageToken', None) if discovery_response else None
            threads: List[Dict] = discovery_response.get('threads', None) if discovery_response else None

            for thread in threads:
                thread_id = thread.get('id', None) if thread else None
                yield Discovery(
                    id=thread_id,
                    type='email_thread'
                )

            if not next_token:
                break
    
    def _get_title(self, messages: Dict) -> str:
        if not messages:
            return
        
        title: Set[str] = set()
        for message in messages:
            part = message.get('payload', None) if message else None
            headers = part.get('headers', []) if part else []
            for header in headers:
                header_name = header.get('name', None)
                if not header_name:
                    continue
                if header_name == 'Subject':
                    subject = header.get('value', None)
                    title.add(subject)

        return '\n\n'.join(title)            

    def _get_owners(self, messages: Dict) -> List[Tuple]:
        if not messages:
            return
        
        owners: List[Tuple] = []
        for message in messages:
            part = message.get('payload', None) if message else None
            headers = part.get('headers', []) if part else []
            for header in headers:
                header_name = header.get('name', None)
                if not header_name:
                    continue
                if header_name == 'From':
                    from_: str = header.get('value', None)
                    if not from_:
                        continue
                    email = from_.split('<')[-1].split('>')[0].strip()
                    name = from_.split('<')[0].strip()
                    owners.append((email, name))
                elif header_name == 'To':
                    to_: str = header.get('value', None)
                    if not to_:
                        continue
                    email = to_.split('<')[-1].split('>')[0].strip()
                    name = to_.split('<')[0].strip()
                    owners.append((email, name))
        return owners

    def _get_body(self, messages: Dict) -> str:
        if not messages:
            return None
        
        body: Set[str] = set()
        for message in messages:
            part = message.get('payload', None) if message else None
            parts = part.get('parts', []) if part else []
            for part in parts:
                if not part:
                    continue
                body_ = part.get('body', None)
                data = body_.get('data', None) if body_ else None
                text = base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4)) if data else None
                text = text.decode('utf-8') if text else None
                if text:
                    mime_type = part.get('mimeType', None) if part else None
                    if mime_type and mime_type.startswith('text/plain'):
                        body.add(text)
        
        return '\n\n'.join(body)
    
    def _get_lut(self, response: Dict) -> int:
        if not response:
            return None
        
        last_updated_timestamp = response.get('internalDate', None) if response else None
        last_updated_timestamp = int(int(last_updated_timestamp) / 1000) if last_updated_timestamp else None
        return last_updated_timestamp

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('google_mail load!')

        response = self._request_session.get(FETCH_THREADS_ENDPOINT.format(id=discovery.id))
        load_response = response.json() if response else None
        if not load_response:
            return
        
        lut = self._get_lut(load_response)
        title = self._get_title(load_response.get('messages', None))
        body = self._get_body(load_response.get('messages', None))
        owners = self._get_owners(load_response.get('messages', None))
        thread = ThreadSection(
            discovery=discovery,
            last_updated_timestamp=lut,
            title=title,
            body=body,
            owners=owners,
        )

        return thread
        