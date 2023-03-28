from typing import Generator

import requests
from app.fetcher.base import DiscoveryResponse, Fetcher, Filter, Item
from app.model.blocks import BlockStream, BodyBlock, CommentBlock, TitleBlock


class Zendesk(Fetcher):
    _INTEGRATION = 'zendesk'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://mimo2079.zendesk.com/oauth/tokens'
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('zendesk discovery!')

        filters = {}
        if filter:
            if filter.next_token:
                filters['page[after]'] = filter.next_token
            if filter.limit:
                filters['page[size]'] = filter.limit

        print('before')
        response = requests.get(
            'https://mimo2079.zendesk.com/api/v2/tickets',
            params={ **filters },
            headers={
                'Authorization': f'Basic '
            }
        )
        discovery_response = response.json()
        print(discovery_response)
        print('after')

        if not discovery_response:
            return None

        tickets = discovery_response.get('tickets', None) if discovery_response else None
        next_token = discovery_response.get('next_page', None) if discovery_response else None

        return DiscoveryResponse(
            integration=self._INTEGRATION,
            icon=self.get_icon(),
            items=[Item(
                id=ticket.get('id', None) if ticket else None,
                title=ticket.get('subject', None) if ticket else None,
                link=f'https://mimo2079.zendesk.com/agent/tickets/{ticket["id"]}' if ticket else None,
                preview=None
            ) for ticket in tickets],
            next_token=next_token
        )
        
    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        session = requests.Session()
        session.headers.update({
            'Authorization': 'Basic '
        })
        response = session.get(f'https://mimo2079.zendesk.com/api/v2/tickets/{id}')
        ticket_response = response.json() if response else None
        ticket = ticket_response.get('ticket', None) if ticket_response else None
        subject = ticket.get('subject', None) if ticket else None
        if subject:
            yield BlockStream(TitleBlock._LABEL, [TitleBlock(title=subject)])
        description = ticket.get('description', None) if ticket else None
        if description:
            for body_stream in self._streamify_blocks(BodyBlock._LABEL, [BodyBlock(body=description)]):
                yield body_stream

        response = session.get(f'https://mimo2079.zendesk.com/api/v2/tickets/{id}/comments')
        comments_response = response.json() if response else None
        comments = comments_response.get('comments', None) if comments_response else None
        comments = comments[1:] if comments else None

        if not comments:
            return
        
        comment_blocks = []
        for comment in comments:
            author_id = comment.get('author_id', None) if comment else None
            author = 'unknown'
            if author_id:
                response = session.get(f'https://mimo2079.zendesk.com/api/v2/users/{author_id}')
                author_response = response.json() if response else None
                author = author_response.get('user', {}).get('name', None) if author_response else None
            comment_blocks.append(CommentBlock(author=author, text=comment.get('plain_body', None)))
        
        for comment_stream in self._streamify_blocks(CommentBlock._LABEL, comment_blocks):
            yield comment_stream