from typing import Dict, Generator, List, Set

from model.blocks import (BlockStream, BodyBlock, CommentBlock, MemberBlock,
                          Relations, TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter
from .model import IntegrationTypes, Page, PageTypes
from .util import generate, get_timestamp_from_format

ZENDESK_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
DISCOVERY_ENDPOINT = 'https://d3v-mimo1489.zendesk.com/api/v2/tickets'
GET_TICKET_ENDPOINT = 'https://d3v-mimo1489.zendesk.com/api/v2/tickets/{id}'
GET_COMMENTS_ENDPOINT = 'https://d3v-mimo1489.zendesk.com/api/v2/tickets/{id}/comments'
USERS_ENDPOINT = 'https://d3v-mimo1489.zendesk.com/api/v2/users/{id}'

class ZendeskSupport(Fetcher):
    _INTEGRATION = 'zendesk_support'

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('zendesk discovery!')

        filters = {}
        if filter:
            if filter.next_token:
                filters['page[after]'] = filter.next_token
            if filter.limit:
                filters['page[size]'] = filter.limit

        response = self._request_session.get(DISCOVERY_ENDPOINT, params={ **filters })
        discovery_response: Dict = response.json() if response and response.status_code == 200 else None
        if not discovery_response:
            return None
        tickets: List[Dict] = discovery_response.get('tickets', None) if discovery_response else None
        next_token: str = discovery_response.get('next_page', None) if discovery_response else None

        return DiscoveryResponse(
            integration_type=IntegrationTypes.CUSTOMER_SUPPORT,
            pages=[Page(
                type=PageTypes.TICKET,
                id=ticket.get('id', None) if ticket else None,
            ) for ticket in tickets],
            next_token=next_token
        )

    def _fetch_user_entity(self, user_entity_map: Dict, id: str) -> entity:
        if not id:
            return None
        if id in user_entity_map:
            return user_entity_map[id]

        response = self._request_session.get(USERS_ENDPOINT.format(id=id))
        user_response: Dict = response.json() if response else None
        user = user_response.get('user', None) if user_response else None
        if not user:
            return None
        user_email = user.get('email', None)
        user_name = user.get('name', None)
        user_entity = entity(id=user_email, value=user_name)
        user_entity_map[id] = user_entity
        return user_entity_map[id]
    
    def _generate_title(self, response: Dict) -> Generator[BlockStream, None, None]:
        ticket: Dict = response.get('ticket', None)
        if not ticket:
            return
        lut = self._get_lut(ticket)
        subject = ticket.get('subject', None)
        if subject:
            yield BlockStream(TitleBlock._LABEL, [TitleBlock(text=subject, last_updated_timestamp=lut)])
    
    def _generate_member(self, ticket_response: Dict, comment_response: Dict, user_entity_map: Dict) -> Generator[BlockStream, None, None]:
        ticket: Dict = ticket_response.get('ticket', None)
        if not ticket:
            return
        lut = self._get_lut(ticket)
        requester = self._fetch_user_entity(user_entity_map, ticket.get('requester_id', None))
        assignee = self._fetch_user_entity(user_entity_map, ticket.get('assignee_id', None))
        member_blocks: Set[MemberBlock] = set()
        if requester:
            member_blocks.add(MemberBlock(name=requester, last_updated_timestamp=lut, relation=Relations.AUTHOR))
        if assignee:
            member_blocks.add(MemberBlock(name=assignee, last_updated_timestamp=lut, relation=Relations.RECIPIENT))

        comments: List[Dict] = comment_response.get('comments', None) if comment_response else None
        member_blocks: Set[MemberBlock] = set()
        for comment in comments:
            comment_last_updated_timestamp = get_timestamp_from_format(comment.get('created_at', None), ZENDESK_TIME_FORMAT) if comment else None
            author_id = comment.get('author_id', None) if comment else None
            author = 'unknown'
            if author_id:
                author = self._fetch_user_entity(user_entity_map, author_id)
                author_member = MemberBlock(name=author, last_updated_timestamp=comment_last_updated_timestamp, relation=Relations.PARTICIPANT)
                if author_member in member_blocks:
                    member_blocks.add(author_member)

        yield from generate(MemberBlock._LABEL, list(member_blocks))

    def _generate_body(self, response: Dict) -> Generator[BlockStream, None, None]:
        ticket: Dict = response.get('ticket', None)
        if not ticket:
            return
        lut = self._get_lut(ticket)
        description = ticket.get('description', None)
        if description:
            yield from generate(BodyBlock._LABEL, [BodyBlock(text=description, last_updated_timestamp=lut)])
        
    def _generate_comment(self, response: Dict, user_entity_map: Dict) -> Generator[BlockStream, None, None]:
        comments = response.get('comments', None)
        comments = comments[1:] if comments else None
        if not comments:
            return
        comment_blocks: List[CommentBlock] = []
        for comment in comments:
            comment_last_updated_timestamp = get_timestamp_from_format(comment.get('created_at', None), ZENDESK_TIME_FORMAT) if comment else None
            author_id = comment.get('author_id', None) if comment else None
            author = 'unknown'
            if author_id:
                author = self._fetch_user_entity(user_entity_map, author_id)
            comment_blocks.append(CommentBlock(author=author, text=comment.get('plain_body', None), last_updated_timestamp=comment_last_updated_timestamp))
        
        yield from generate(CommentBlock._LABEL, comment_blocks)
    
    def _get_lut(self, response: Dict) -> int:
        if not response:
            return None
        ticket: Dict = response.get('ticket', None)
        return get_timestamp_from_format(ticket.get('updated_at', None), ZENDESK_TIME_FORMAT) if ticket else None
    
    def fetch(self, page: Page) -> Generator[BlockStream, None, None]:
        print('zendesk fetch!')

        response = self._request_session.get(GET_TICKET_ENDPOINT.format(id=page.id))
        ticket_response = response.json() if response and response.status_code == 200 else None
        yield from self._generate_title(ticket_response)
        yield from self._generate_body(ticket_response)

        user_entity_map: Dict[str, entity] = {}
        response = self._request_session.get(GET_COMMENTS_ENDPOINT.format(id=page.id))
        comment_response = response.json() if response and response.status_code == 200 else None
        yield from self._generate_comment(comment_response, user_entity_map)
        yield from self._generate_member(ticket_response, comment_response, user_entity_map)
