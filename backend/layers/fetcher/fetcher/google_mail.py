import base64
from typing import Generator, List

import requests
from graph.blocks import (BlockStream, BodyBlock, MemberBlock, Relations,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item


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
    
    def _fetch_thread(self, id: str) -> dict:
        response = requests.get(
            f'https://www.googleapis.com/gmail/v1/users/me/threads/{id}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            }
        )

        load_response = response.json() if response else None
        last_updated_timestamp = load_response.get('internalDate', None) if load_response else None
        last_updated_timestamp = int(int(last_updated_timestamp) / 1000) if last_updated_timestamp else None
        messages = load_response.get('messages', None) if load_response else None
        if not messages:
            return None
        
        for message in messages:
            last_updated_timestamp = message.get('internalDate', None) if message else None
            last_updated_timestamp = int(int(last_updated_timestamp) / 1000) if last_updated_timestamp else None
            message['last_updated_timestamp'] = last_updated_timestamp
        return messages

    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        print('google_mail load!')
        self.auth.refresh()
        messages = self._fetch_thread(id)
        if not messages:
            return
        
        member_blocks_map: dict[str, MemberBlock] = {}
        title_blocks_map: dict[str, TitleBlock] = {}
        for message in messages:
            part = message.get('payload', None) if message else None
            headers = part.get('headers', []) if part else []
            last_updated_timestamp = message.get('last_updated_timestamp', None) if message else None
            for header in headers:
                header_name = header.get('name', None)
                if not header_name:
                    continue
                if header_name == 'Subject':
                    subject = header.get('value', None)
                    if subject and subject not in title_blocks_map:
                        title_blocks_map[subject] = TitleBlock(text=subject, last_updated_timestamp=last_updated_timestamp)
                elif header_name == 'From':
                    from_: str = header.get('value', None)
                    if not from_:
                        continue
                    email = from_.split('<')[-1].split('>')[0].strip()
                    name = from_.split('<')[0].strip()
                    if email not in member_blocks_map:
                        name_entity = entity(id=email, value=name)
                        member_blocks_map[email] = MemberBlock(last_updated_timestamp=last_updated_timestamp, name=name_entity, relation=Relations.AUTHOR)
                elif header_name == 'To':
                    to_: str = header.get('value', None)
                    if not to_:
                        continue
                    email = to_.split('<')[-1].split('>')[0].strip()
                    name = to_.split('<')[0].strip()
                    if email not in member_blocks_map:
                        name_entity = entity(id=email, value=None)
                        member_blocks_map[email] = MemberBlock(last_updated_timestamp=last_updated_timestamp, name=name_entity, relation=Relations.RECIPIENT)

        for member_stream in self._streamify_blocks(MemberBlock._LABEL, member_blocks_map.values()):
            yield member_stream

        for title_stream in self._streamify_blocks(TitleBlock._LABEL, title_blocks_map.values()):
            yield title_stream
        
        body_blocks: List[BodyBlock] = []
        for message in messages:
            message_parts = [message.get('payload', None)] if message else None
            if not message_parts:
                continue

            last_updated_timestamp = message.get('last_updated_timestamp', None) if message else None
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
                        body_blocks.append(BodyBlock(text=text, last_updated_timestamp=last_updated_timestamp))

                parts = part.get('parts', None)
                if parts:
                    message_parts[0:0] = parts

            for body_stream in self._streamify_blocks(BodyBlock._LABEL, body_blocks):
                yield body_stream
