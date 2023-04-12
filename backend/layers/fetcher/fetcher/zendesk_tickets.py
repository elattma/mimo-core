from typing import Any, Generator, List

import requests
from graph.blocks import (BlockStream, BodyBlock, CommentBlock, MemberBlock,
                          Relations, TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item

ZENDESK_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class Zendesk(Fetcher):
    _INTEGRATION = 'zendesk'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://mimo8561.zendesk.com/oauth/tokens'
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('zendesk discovery!')

        filters = {}
        if filter:
            if filter.next_token:
                filters['page[after]'] = filter.next_token
            if filter.limit:
                filters['page[size]'] = filter.limit

        response = requests.get(
            'https://mimo8561.zendesk.com/api/v2/tickets',
            params={ **filters },
            headers={
                'Authorization': f'Basic YWRtaW5AbWltby50ZWFtOkBANVoyQVdrUjJZYkEzaw=='
            }
        )
        discovery_response = response.json() if response else None
        tickets = discovery_response.get('tickets', None) if discovery_response else None
        next_token = discovery_response.get('next_page', None) if discovery_response else None

        return DiscoveryResponse(
            items=[Item(
                integration=self._INTEGRATION,
                id=ticket.get('id', None) if ticket else None,
                title=ticket.get('subject', None) if ticket else None,
                icon=self.get_icon(),
                link=f'https://mimo8561.zendesk.com/agent/tickets/{ticket["id"]}' if ticket else None,
            ) for ticket in tickets],
            next_token=next_token
        )
    
    @staticmethod
    def _fetch_ticket(session: requests.Session, id: str) -> dict:
        if not (session and id):
            return None
        
        response = session.get(f'https://mimo8561.zendesk.com/api/v2/tickets/{id}')
        ticket_response = response.json() if response else None
        ticket = ticket_response.get('ticket', None) if ticket_response else None
        return ticket

    @staticmethod
    def _fetch_user_entity(session: requests.Session, id: str) -> entity:
        if not (session and id):
            return None

        response = session.get(f'https://mimo8561.zendesk.com/api/v2/users/{id}')
        user_response = response.json() if response else None
        user = user_response.get('user', None) if user_response else None
        user_name = user.get('name', None) if user else None
        user_email = user.get('email', None) if user else None
        return entity(id=user_email, value=user_name)
    
    @staticmethod
    def _fetch_comments(session: requests.Session, id: str) -> List[Any]:
        if not (session and id):
            return None

        response = session.get(f'https://mimo8561.zendesk.com/api/v2/tickets/{id}/comments')
        comments_response = response.json() if response else None
        comments = comments_response.get('comments', None) if comments_response else None
        comments = comments[1:] if comments else None
        return comments
    
    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        print('zendesk fetch!')

        session = requests.Session()
        session.headers.update({
            'Authorization': 'Basic YWRtaW5AbWltby50ZWFtOkBANVoyQVdrUjJZYkEzaw=='
        })
        ticket = Zendesk._fetch_ticket(session, id)
        ticket_last_updated_timestamp = self._get_timestamp_from_format(ticket.get('updated_at', None), ZENDESK_TIME_FORMAT) if ticket else None
        subject = ticket.get('subject', None) if ticket else None
        member_blocks_map: dict[str, MemberBlock] = {}
        
        requester = Zendesk._fetch_user_entity(session, ticket.get('requester_id', None)) if ticket else None
        assignee = Zendesk._fetch_user_entity(session, ticket.get('assignee_id', None)) if ticket else None
        if requester:
            member_blocks_map[requester] = MemberBlock(name=requester, last_updated_timestamp=ticket_last_updated_timestamp, relation=Relations.AUTHOR)
        if assignee:
            member_blocks_map[assignee] = MemberBlock(name=assignee, last_updated_timestamp=ticket_last_updated_timestamp, relation=Relations.RECIPIENT)

        if subject:
            yield BlockStream(TitleBlock._LABEL, [TitleBlock(text=subject, last_updated_timestamp=ticket_last_updated_timestamp)])
        description = ticket.get('description', None) if ticket else None
        if description:
            for body_stream in self._streamify_blocks(BodyBlock._LABEL, [BodyBlock(text=description, last_updated_timestamp=ticket_last_updated_timestamp)]):
                yield body_stream

        comments = Zendesk._fetch_comments(session, id)
        comment_blocks = []
        for comment in comments:
            comment_last_updated_timestamp = self._get_timestamp_from_format(comment.get('created_at', None), ZENDESK_TIME_FORMAT) if comment else None
            author_id = comment.get('author_id', None) if comment else None
            author = 'unknown'
            if author_id:
                author = Zendesk._fetch_user_entity(session, author_id)
                if author:
                    if author not in member_blocks_map:
                        member_blocks_map[author] = MemberBlock(name=author, last_updated_timestamp=comment_last_updated_timestamp, relation=Relations.PARTICIPANT)
                    else:
                        member_blocks_map[author].last_updated_timestamp = max(comment_last_updated_timestamp, member_blocks_map[author].last_updated_timestamp)
                    
            comment_blocks.append(CommentBlock(author=author, text=comment.get('plain_body', None), last_updated_timestamp=comment_last_updated_timestamp))
        
        for comment_stream in self._streamify_blocks(CommentBlock._LABEL, comment_blocks):
            yield comment_stream

        if len(member_blocks_map) > 0:
            for member_stream in self._streamify_blocks(MemberBlock._LABEL, member_blocks_map.values()):
                yield member_stream