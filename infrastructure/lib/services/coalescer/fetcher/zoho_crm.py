from datetime import datetime
from typing import Dict, Generator, List
from urllib.parse import quote

from model.blocks import (Block, BlockStream, CommentBlock, ContactBlock,
                          DealBlock, TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter
from .model import IntegrationTypes, Page, PageTypes
from .util import generate, get_entity

COQL_ENDPOINT = 'https://www.zohoapis.com/crm/v3/coql'
ACCOUNTS_ENDPOINT = 'https://www.zohoapis.com/crm/v3/Accounts/{id}'
NOTES_ENDPOINT = 'https://www.zohoapis.com/crm/v3/Accounts/{id}/Notes'
CONTACTS_ENDPOINT = 'https://www.zohoapis.com/crm/v3/Contacts/search'
DEALS_ENDPOINT = 'https://www.zohoapis.com/crm/v3/Deals/search'

class ZohoCrm(Fetcher):
    _INTEGRATION = 'zoho_crm'

    def init(self, access_token: str, **kwargs):
        super().init(access_token, **kwargs)
        self._request_session.headers.update({
            'Authorization': f'Zoho-oauthtoken {access_token}'
        })

    def get_timestamp_from_format(self, timestamp_str: str, format: str = None) -> int:
        if not timestamp_str:
            return None
        datetime_str = datetime.fromisoformat(timestamp_str)
        return int(datetime_str.timestamp()) if datetime_str else None

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('zoho discovery!')

        offset = filter.next_token if filter and filter.next_token else 0
        limit = filter.limit if filter and filter.limit else 100
        filters = {
            'select_query': f'select id, Account_Name from Accounts where Account_Name like \'%\' order by Account_Name asc limit {offset}, {limit}'
        }
        if filter:
            if filter.next_token:
                filters['page'] = filter.next_token
            if filter.limit:
                filters['per_page'] = filter.limit

        response = self._request_session.post(COQL_ENDPOINT, json={ **filters })
        discovery_response: Dict = response.json() if response and response.status_code == 200 else None
        accounts: List[Dict] = discovery_response.get('data', None) if discovery_response else None

        return DiscoveryResponse(
            integration_type=IntegrationTypes.CRM,
            pages=[Page(
                type=PageTypes.ACCOUNT,
                id=account.get('id', None) if account else None,
            ) for account in accounts if account] if accounts else [],
            next_token=(offset + limit) if accounts and len(accounts) > 0 else None
        )
    
    def _generate_title(self, account: Dict) -> Generator[BlockStream, None, None]:
        account_lut = self.get_timestamp_from_format(account.get('Modified_Time', None))
        account_name = account.get('Account_Name', None)
        title_blocks = []
        title_blocks.append(TitleBlock(
            last_updated_timestamp=account_lut, 
            text=account_name
        ))
        yield from generate(TitleBlock._LABEL, title_blocks)

    def _generate_comment(self, response: Dict) -> Generator[BlockStream, None, None]:
        notes = response.get('data', None) if response else None
        comment_blocks = []
        if notes:
            for note in notes:
                if not note:
                    continue
                author = note.get('Created_By', {})
                author_entity = get_entity(author.get('email', None), author.get('name', None))
                text = f'{note.get("Note_Title", "")}: {note.get("Note_Content", "")}'
                last_updated_timestamp = self.get_timestamp_from_format(note.get('Modified_Time', None))
                comment_blocks.append(CommentBlock(author=author_entity, text=text, last_updated_timestamp=last_updated_timestamp))
            
            yield from generate(CommentBlock._LABEL, comment_blocks)

    def _generate_contact(self, response: Dict) -> Generator[BlockStream, None, None]:
        contacts = response.get('data', None) if response else None
        contact_blocks = []
        if contacts:
            for contact in contacts:
                if not contact:
                    continue
                name_entity = get_entity(contact.get('Email', None), contact.get('Full_Name', None))
                created_by = contact.get('Created_By', {})
                created_by_entity = get_entity(created_by.get('email', None), created_by.get('name', None))
                department = contact.get('Department', None)
                title = contact.get('Title', None)
                lead_source = contact.get('Lead_Source', None)
                last_updated_timestamp = self.get_timestamp_from_format(contact.get('Modified_Time', None))
                contact_blocks.append(ContactBlock(
                    name=name_entity,
                    created_by=created_by_entity,
                    department=department,
                    title=title,
                    lead_source=lead_source,
                    last_updated_timestamp=last_updated_timestamp
                ))

            yield from generate(ContactBlock._LABEL, contact_blocks)
    
    def _generate_deal(self, response: Dict) -> Generator[BlockStream, None, None]:
        deals = response.get('data', None) if response else None
        deal_blocks = []
        if deals:
            for deal in deals:
                if not deal:
                    continue
                owner = deal.get('Owner', {})
                owner_entity = get_entity(owner.get('email', None), owner.get('name', None))
                deal_entity = get_entity(deal.get('id', None), deal.get('Deal_Name', None))
                contact_id = deal.get('Contact_Name', {}).get('id', None)
                contact_entity = get_entity(contact_id, None)
                type = deal.get('Type', None)
                stage = deal.get('Stage', None)
                close_date = deal.get('Closing_Date', None)
                amount = int(deal.get('Amount')) if deal.get('Amount', None) else None
                probability = int(deal.get('Probability')) if deal.get('Probability', None) else None
                last_updated_timestamp = self.get_timestamp_from_format(deal.get('Modified_Time', None))
                deal_blocks.append(DealBlock(
                    owner=owner_entity, 
                    name=deal_entity, 
                    contact=contact_entity, 
                    type=type, stage=stage, 
                    close_date=close_date, 
                    amount=amount, 
                    probability=probability,
                    last_updated_timestamp=last_updated_timestamp
                ))
            yield from generate(DealBlock._LABEL, deal_blocks)

    def fetch(self, page: Page) -> Generator[Block, None, None]:
        print('zoho fetch!')
        response = self._request_session.get(ACCOUNTS_ENDPOINT.format(id=page.id))
        account_response = response.json() if response and response.status_code == 200 else None
        accounts: List[Dict] = account_response.get('data', None) if account_response else None
        account: Dict = accounts[0] if accounts else None
        if not account:
            return
        yield from self._generate_title(account)

        account_name: str = account.get('Account_Name', None)
        quoted = account_name.replace('(', '\(').replace(')', '\)').replace(',', '\,')
        quoted_starts_with = quote(quoted.split(' ')[0]) if quoted else None

        # TODO: use next tokens to grab all notes
        response = self._request_session.get(
            NOTES_ENDPOINT.format(id=page.id),
            params={
                'fields': 'id,Note_Title,Note_Content,Created_By,Created_Time,Modified_Time'
            }
        )
        notes_response: Dict = response.json() if response and response.status_code == 200 else None
        yield from self._generate_comment(notes_response)

        response = self._request_session.get(
            CONTACTS_ENDPOINT,
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})'
            }
        )
        contacts_response = response.json() if response and response.status_code == 200 else None
        yield from self._generate_contact(contacts_response)

        response = self._request_session.get(
            DEALS_ENDPOINT,
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})',
            }
        )
        list_deals_response = response.json() if response and response.status_code == 200 else None
        yield from self._generate_deal(list_deals_response)