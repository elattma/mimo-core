from typing import Generator

import requests
from app.fetcher.base import (Block, BodyBlock, DiscoveryResponse, Fetcher,
                              Filter, Item, TitleBlock)


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

        response = requests.get(
            'https://mimo2079.zendesk.com/api/v2/tickets',
            params={ **filters },
            headers={
                'Authorization': f'Basic access_token_test='
            }
        )
        discovery_response = response.json()

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
        
    def fetch(self, id: str) -> Generator[Block, None, None]:
        response = requests.get(
            f'https://mimo2079.zendesk.com/api/v2/tickets/{id}',
            headers={
                'Authorization': f'Basic access_token_test='
            }
        )
        ticket_response = response.json() if response else None
        ticket = ticket_response.get('ticket', None) if ticket_response else None
        subject = ticket.get('subject', None) if ticket else None
        if subject:
            yield TitleBlock(title=subject)
        description = ticket.get('description', None) if ticket else None
        if description:
            for text in self._merge_split_texts([description]):
                yield BodyBlock(body=text)

        response = requests.get(
            f'https://mimo2079.zendesk.com/api/v2/tickets/{id}/comments',
            headers={
                'Authorization': f'Basic access_token_test='
            }
        )
        comments_response = response.json() if response else None
        comments = comments_response.get('comments', None) if comments_response else None
        comments = comments[1:] if comments else None

        if not comments:
            return
        
        print(comments)

zendesk = Zendesk()
d = zendesk.discover()
print(d)
for x in d.items:
    print(x)
    for y in zendesk.fetch(x.id):
        print(y)