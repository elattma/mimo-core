from typing import Generator
from urllib.parse import quote

import requests
from app.fetcher.base import (Block, CommentBlock, ContactBlock, DealBlock,
                              DiscoveryResponse, Fetcher, Filter, Item)


class Zoho(Fetcher):
    _INTEGRATION = 'zoho'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://accounts.zoho.com/oauth/v2/token',
            'refresh_endpoint': 'https://accounts.zoho.com/oauth/v2/token',
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('zoho discovery!')

        offset = filter.next_token if filter and filter.next_token else 1
        limit = filter.limit if filter and filter.limit else 10
        filters = {
            'select_query': f'select id, Account_Name from Accounts where Account_Name like \'%\' order by Account_Name asc limit {offset}, {limit}'
        }
        if filter:
            if filter.next_token:
                filters['page'] = filter.next_token
            if filter.limit:
                filters['per_page'] = filter.limit

        succeeded = self.auth.refresh()
        if not succeeded:
            print('failed to refresh google mail token')
            return None
        
        response = requests.post(
            'https://www.zohoapis.com/crm/v3/coql',
            json={ **filters },
            headers={
                'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
            }
        )
        discovery_response = response.json() if response and response.status_code == 200 else None
        accounts = discovery_response.get('data', None) if discovery_response else None

        response = requests.get(
            'https://www.zohoapis.com/crm/v2/org',
            headers={
                'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
            }
        )
        org_response = response.json() if response else None
        orgs = org_response.get('org', None) if org_response else None
        org_id = orgs[0].get('domain_name', None) if orgs and len(orgs) > 0 else None

        return DiscoveryResponse(
            integration=self._INTEGRATION, 
            icon=self.get_icon(),
            items=[Item(
                id=account.get('id', None) if account else None,
                title=account.get('Account_Name', None) if account else None,
                link=f'https://crm.zoho.com/crm/{org_id}/tab/Accounts/{account["id"]}' if account and org_id else None,
                preview=None
            ) for account in accounts] if accounts else [],
            next_token=(offset + limit) if accounts and len(accounts) > 0 else None
        )

    # TODO: move to bulk read
    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('zoho fetch!')

        session = requests.session()
        session.headers.update({
            'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
        })
        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Accounts/{id}',
        )
        account_response = response.json() if response and response.status_code == 200 else None
        accounts = account_response.get('data', None) if account_response else None
        account = accounts[0] if accounts else None
        owner = account.get('Owner', {}).get('name', None) if account else None
        if not account:
            return

        # TODO: use next tokens to grab all notes
        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Accounts/{id}/Notes',
            params={
                'fields': 'id,Note_Title,Note_Content,Created_Time,Modified_Time'
            },
        )
        notes_response = response.json() if response and response.status_code == 200 else None
        notes = notes_response.get('data', None) if notes_response else None
        comment_blocks = [CommentBlock(author=owner, text=(f'{note.get("Note_Title", "")}: {note.get("Note_Content", "")}')) for note in notes] if notes else []
        for comment_stream in self._streamify_blocks(comment_blocks):
            yield comment_stream

        account_name: str = account['Account_Name']
        quoted = account_name.replace('(', '\(').replace(')', '\)').replace(',', '\,')
        quoted_starts_with = quote(quoted.split(' ')[0]) if quoted else None
        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Deals/search',
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})',
            }
        )
        list_deals_response = response.json() if response and response.status_code == 200 else None
        deals = list_deals_response.get('data', None) if list_deals_response else None # TODO: too many api calls to grab all notes for each deal
        deal_blocks = [DealBlock(
            owner=deal.get('Owner', {}).get('name', None),
            name=deal.get('Deal_Name', None),
            contact=deal.get('Contact_Name', {}).get('name', None),
            type=deal.get('Type', None),
            stage=deal.get('Stage', None),
            close_date=deal.get('Closing_Date', None),
            amount=int(deal.get('Amount')) if deal.get('Amount', None) else None,
            probability=int(deal.get('Probability')) if deal.get('Probability', None) else None,
        ) for deal in deals] if deals else []
        for deal_stream in self._streamify_blocks(deal_blocks):
            yield deal_stream

        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Contacts/search',
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})',
            }
        )
        contacts_response = response.json() if response and response.status_code == 200 else None
        contacts = contacts_response.get('data', None) if contacts_response else None
        contact_blocks = [ContactBlock(
            name=contact.get('Full_Name', None),
            created_by=contact.get('Created_By', {}).get('name', None),
            department=contact.get('Department', None),
            title=contact.get('Title', None),
            lead_source=contact.get('Lead_Source', None),
        ) for contact in contacts] if contacts else []
        for contact_stream in self._streamify_blocks(contact_blocks):
            yield contact_stream
