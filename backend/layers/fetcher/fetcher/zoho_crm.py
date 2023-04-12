from datetime import datetime
from typing import Generator, List
from urllib.parse import quote

import requests
from graph.blocks import (Block, CommentBlock, ContactBlock, DealBlock,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item


class Zoho(Fetcher):
    _INTEGRATION = 'zoho'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://accounts.zoho.com/oauth/v2/token',
            'refresh_endpoint': 'https://accounts.zoho.com/oauth/v2/token',
        }
    
    def _get_timestamp_from_format(self, timestamp_str: str, format: str = None) -> int:
        if not timestamp_str:
            return None
        datetime_str = datetime.fromisoformat(timestamp_str)
        return int(datetime_str.timestamp()) if datetime_str else None

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
            items=[Item(
                integration=self._INTEGRATION, 
                id=account.get('id', None) if account else None,
                title=account.get('Account_Name', None) if account else None,
                icon=self.get_icon(),
                link=f'https://crm.zoho.com/crm/{org_id}/tab/Accounts/{account["id"]}' if account and org_id else None,
            ) for account in accounts] if accounts else [],
            next_token=(offset + limit) if accounts and len(accounts) > 0 else None
        )
    
    def _get_entity(self, id: str = None, name: str = None) -> entity:
        if not (id and name):
            return None
        return entity(id=id, value=name)

    # TODO: move to bulk read
    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('zoho fetch!')

        session = requests.session()
        session.headers.update({
            'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
        })
        response = session.get(f'https://www.zohoapis.com/crm/v3/Accounts/{id}')
        account_response = response.json() if response and response.status_code == 200 else None
        accounts = account_response.get('data', None) if account_response else None
        account = accounts[0] if accounts else None
        owner = account.get('Owner', {}).get('name', None) if account else None
        if not account:
            return
        
        account_name: str = account['Account_Name']
        title_blocks: List[TitleBlock] = []
        account_last_updated_timestamp = self._get_timestamp_from_format(account.get('Modified_Time', None))
        title_blocks.append(TitleBlock(
            last_updated_timestamp=account_last_updated_timestamp, 
            text=account_name
        ))
        for title_stream in self._streamify_blocks(TitleBlock._LABEL, title_blocks):
            yield title_stream

        quoted = account_name.replace('(', '\(').replace(')', '\)').replace(',', '\,')
        quoted_starts_with = quote(quoted.split(' ')[0]) if quoted else None

        # TODO: use next tokens to grab all notes
        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Accounts/{id}/Notes',
            params={
                'fields': 'id,Note_Title,Note_Content,Created_By,Created_Time,Modified_Time'
            },
        )
        notes_response = response.json() if response and response.status_code == 200 else None
        notes = notes_response.get('data', None) if notes_response else None
        comment_blocks: List[CommentBlock] = []
        if notes:
            for note in notes:
                if not note:
                    continue
                author = note.get('Created_By', {})
                author_entity = self._get_entity(author.get('email', None), author.get('name', None))
                text = f'{note.get("Note_Title", "")}: {note.get("Note_Content", "")}'
                last_updated_timestamp = self._get_timestamp_from_format(note.get('Modified_Time', None))
                comment_blocks.append(CommentBlock(author=author_entity, text=text, last_updated_timestamp=last_updated_timestamp))
            
            for comment_stream in self._streamify_blocks(CommentBlock._LABEL, comment_blocks):
                yield comment_stream

        contact_id_entity_map: dict[str, entity] = {}
        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Contacts/search',
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})',
            }
        )
        contacts_response = response.json() if response and response.status_code == 200 else None
        contacts = contacts_response.get('data', None) if contacts_response else None
        contact_blocks = []
        if contacts:
            for contact in contacts:
                if not contact:
                    continue
                name_entity = self._get_entity(contact.get('Email', None), contact.get('Full_Name', None))
                if name_entity:
                    contact_id_entity_map[contact.get('id', None)] = name_entity
                created_by = contact.get('Created_By', {})
                created_by_entity = self._get_entity(created_by.get('email', None), created_by.get('name', None))
                department = contact.get('Department', None)
                title = contact.get('Title', None)
                lead_source = contact.get('Lead_Source', None)
                last_updated_timestamp = self._get_timestamp_from_format(contact.get('Modified_Time', None))
                contact_blocks.append(ContactBlock(
                    name=name_entity,
                    created_by=created_by_entity,
                    department=department,
                    title=title,
                    lead_source=lead_source,
                    last_updated_timestamp=last_updated_timestamp
                ))

            for contact_stream in self._streamify_blocks(ContactBlock._LABEL, contact_blocks):
                yield contact_stream

        response = session.get(
            f'https://www.zohoapis.com/crm/v3/Deals/search',
            params={
                'criteria': f'(Account_Name:starts_with:{quoted_starts_with})',
            }
        )
        list_deals_response = response.json() if response and response.status_code == 200 else None
        deals = list_deals_response.get('data', None) if list_deals_response else None # TODO: too many api calls to grab all notes for each deal
        deal_blocks: List[DealBlock] = []
        if deals:
            for deal in deals:
                if not deal:
                    continue
                owner = deal.get('Owner', {})
                owner_entity = self._get_entity(owner.get('email', None), owner.get('name', None))
                deal_entity = self._get_entity(deal.get('id', None), deal.get('Deal_Name', None))
                contact_id = deal.get('Contact_Name', {}).get('id', None)
                if contact_id:
                    contact_entity = contact_id_entity_map.get(contact_id, None)
                type = deal.get('Type', None)
                stage = deal.get('Stage', None)
                close_date = deal.get('Closing_Date', None)
                amount = int(deal.get('Amount')) if deal.get('Amount', None) else None
                probability = int(deal.get('Probability')) if deal.get('Probability', None) else None
                last_updated_timestamp = self._get_timestamp_from_format(deal.get('Modified_Time', None))
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
            for deal_stream in self._streamify_blocks(DealBlock._LABEL, deal_blocks):
                yield deal_stream
