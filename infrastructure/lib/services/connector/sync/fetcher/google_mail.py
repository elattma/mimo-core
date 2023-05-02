import base64
from typing import Dict, Generator, List, Set

from model.blocks import (BlockStream, BodyBlock, MemberBlock, Relations,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter
from .model import IntegrationTypes, Page, PageTypes
from .util import generate

DISCOVERY_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads'
FETCH_THREADS_ENDPOINT = 'https://www.googleapis.com/gmail/v1/users/me/threads/{id}'

class GoogleMail(Fetcher):
    _INTEGRATION = 'google_mail'

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('google_mail discovery!')

        filters = {}
        if filter:
            if filter.next_token:
                filters['pageToken'] = filter.next_token
            if filter.limit:
                filters['maxResults'] = filter.limit

        response = self._request_session.get(DISCOVERY_ENDPOINT, params={ **filters })
        discovery_response: Dict = response.json() if response else None
        if not discovery_response:
            return None
        
        next_token: str = discovery_response.get('nextPageToken', None)
        threads: List[Dict] = discovery_response.get('threads', [])

        return DiscoveryResponse(
            integration_type=IntegrationTypes.MAIL,
            pages=[Page(
                type=PageTypes.MAIL_THREAD,
                id=thread.get('id', None) if thread else None,
            ) for thread in threads],
            next_token=next_token
        )
    
    def _generate_title(self, response: Dict) -> Generator[BlockStream, None, None]:
        messages = response.get('messages', None) if response else None
        if not messages:
            return
        
        title_blocks: Set[TitleBlock] = set()
        for message in messages:
            lut = self._get_lut(message)
            part = message.get('payload', None) if message else None
            headers = part.get('headers', []) if part else []
            for header in headers:
                header_name = header.get('name', None)
                if not header_name:
                    continue
                if header_name == 'Subject':
                    subject = header.get('value', None)
                    title_blocks.add(TitleBlock(text=subject, last_updated_timestamp=lut))
            
        yield from generate(TitleBlock._LABEL, title_blocks)

    def _generate_member(self, response: Dict) -> Generator[BlockStream, None, None]:
        messages = response.get('messages', None) if response else None
        if not messages:
            return
        
        member_blocks: Set[MemberBlock] = set()
        for message in messages:
            lut = self._get_lut(message)
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
                    member_blocks.add(MemberBlock(last_updated_timestamp=lut, name=entity(id=email, value=name), relation=Relations.AUTHOR))
                elif header_name == 'To':
                    to_: str = header.get('value', None)
                    if not to_:
                        continue
                    email = to_.split('<')[-1].split('>')[0].strip()
                    name = to_.split('<')[0].strip()
                    member_blocks.add(MemberBlock(last_updated_timestamp=lut, name=entity(id=email, value=None), relation=Relations.RECIPIENT))
        
        yield from generate(MemberBlock._LABEL, member_blocks)

    def _generate_body(self, response: Dict) -> Generator[BlockStream, None, None]:
        messages = response.get('messages', None) if response else None
        if not messages:
            return
        
        body_blocks: Set[BodyBlock] = set()
        for message in messages:
            lut = self._get_lut(message)
            part: Dict = message.get('payload', None) if message else None
            parts: List[Dict] = part.get('parts', []) if part else []
            for part in parts:
                if not part:
                    continue
                body: Dict = part.get('body', None)
                data = body.get('data', None) if body else None
                text = base64.urlsafe_b64decode(data + '=' * (4 - len(data) % 4)) if data else None
                text = text.decode('utf-8') if text else None
                if text:
                    mime_type = part.get('mimeType', None) if part else None
                    if mime_type and mime_type.startswith('text/plain'):
                        body_blocks.add(BodyBlock(text=text, last_updated_timestamp=lut))

        yield from generate(BodyBlock._LABEL, body_blocks)
    
    def _get_lut(self, response: Dict) -> int:
        if not response:
            return None
        
        last_updated_timestamp = response.get('internalDate', None) if response else None
        last_updated_timestamp = int(int(last_updated_timestamp) / 1000) if last_updated_timestamp else None
        return last_updated_timestamp

    def fetch(self, page: Page) -> Generator[BlockStream, None, None]:
        print('google_mail load!')

        response = self._request_session.get(FETCH_THREADS_ENDPOINT.format(id=page.id))
        load_response = response.json() if response else None
        if not load_response:
            return
        yield from self._generate_title(load_response)
        yield from self._generate_member(load_response)
        yield from self._generate_body(load_response)
        