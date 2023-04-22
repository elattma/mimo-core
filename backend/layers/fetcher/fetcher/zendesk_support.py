from typing import Any, Generator, List, Set

import requests
from graph.blocks import (BlockStream, BodyBlock, CommentBlock, MemberBlock,
                          Relations, TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item

ZENDESK_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

class ZendeskSupport(Fetcher):
    _INTEGRATION = 'zendesk_support'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://mimo1489.ZendeskSupport.com/oauth/tokens'
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
            'https://mimo1489.ZendeskSupport.com/api/v2/tickets',
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
                link=f'https://mimo1489.ZendeskSupport.com/agent/tickets/{ticket["id"]}' if ticket else None,
            ) for ticket in tickets],
            next_token=next_token
        )
    
    @staticmethod
    def _fetch_ticket(session: requests.Session, id: str) -> dict:
        if not (session and id):
            return None
        
        response = session.get(f'https://mimo1489.ZendeskSupport.com/api/v2/tickets/{id}')
        ticket_response = response.json() if response else None
        ticket = ticket_response.get('ticket', None) if ticket_response else None
        return ticket

    @staticmethod
    def _fetch_user_entity(session: requests.Session, id: str) -> entity:
        if not (session and id):
            return None

        response = session.get(f'https://mimo1489.ZendeskSupport.com/api/v2/users/{id}')
        user_response = response.json() if response else None
        user = user_response.get('user', None) if user_response else None
        user_name = user.get('name', None) if user else None
        user_email = user.get('email', None) if user else None
        return entity(id=user_email, value=user_name)
    
    @staticmethod
    def _fetch_comments(session: requests.Session, id: str) -> List[Any]:
        if not (session and id):
            return None

        response = session.get(f'https://mimo1489.ZendeskSupport.com/api/v2/tickets/{id}/comments')
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
        ticket = ZendeskSupport._fetch_ticket(session, id)
        ticket_last_updated_timestamp = self._get_timestamp_from_format(ticket.get('updated_at', None), ZENDESK_TIME_FORMAT) if ticket else None
        subject = ticket.get('subject', None) if ticket else None
        member_blocks: Set[MemberBlock] = set()
        
        requester = ZendeskSupport._fetch_user_entity(session, ticket.get('requester_id', None)) if ticket else None
        assignee = ZendeskSupport._fetch_user_entity(session, ticket.get('assignee_id', None)) if ticket else None
        if requester:
            member_blocks.add(MemberBlock(name=requester, last_updated_timestamp=ticket_last_updated_timestamp, relation=Relations.AUTHOR))
        if assignee:
            member_blocks.add(MemberBlock(name=assignee, last_updated_timestamp=ticket_last_updated_timestamp, relation=Relations.RECIPIENT))

        if subject:
            yield BlockStream(TitleBlock._LABEL, [TitleBlock(text=subject, last_updated_timestamp=ticket_last_updated_timestamp)])
        description = ticket.get('description', None) if ticket else None
        if description:
            yield from self._generate(BodyBlock._LABEL, [BodyBlock(text=description, last_updated_timestamp=ticket_last_updated_timestamp)])

        comments = ZendeskSupport._fetch_comments(session, id)
        comment_blocks = []
        if comments:
            for comment in comments:
                comment_last_updated_timestamp = self._get_timestamp_from_format(comment.get('created_at', None), ZENDESK_TIME_FORMAT) if comment else None
                author_id = comment.get('author_id', None) if comment else None
                author = 'unknown'
                if author_id:
                    author = ZendeskSupport._fetch_user_entity(session, author_id)
                    author_member = MemberBlock(name=author, last_updated_timestamp=comment_last_updated_timestamp, relation=Relations.PARTICIPANT)
                    if author_member in member_blocks:
                        member_blocks.add(author_member)
                        
                comment_blocks.append(CommentBlock(author=author, text=comment.get('plain_body', None), last_updated_timestamp=comment_last_updated_timestamp))
        
        yield from self._generate(CommentBlock._LABEL, comment_blocks)
        yield from self._generate(MemberBlock._LABEL, list(member_blocks))
