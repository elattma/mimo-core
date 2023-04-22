from datetime import datetime
from typing import Dict, Generator, List
from urllib.parse import quote

import requests
from graph.blocks import (Block, CommentBlock, ContactBlock, DealBlock,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item

BASE_URL = 'https://mimo2-dev-ed.develop.my.salesforce.com'

class SalesforceCrm(Fetcher):
    _INTEGRATION = 'salesforce_crm'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': f'{BASE_URL}/services/oauth2/token',
            'refresh_endpoint': f'{BASE_URL}/services/oauth2/token',
        }
    
    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('salesforce crm discovery!')

        succeeded = self.auth.refresh()
        if not succeeded:
            return None
        
        suffix = '/services/data/v57.0/query'
        limit = 100
        if filter:
            if filter.next_token:
                suffix = filter.next_token
            if filter.limit:
                limit = filter.limit
        query = f'SELECT Id, Name FROM Account LIMIT {limit}'
        response = requests.get(
            f'{BASE_URL}{suffix}',
            headers={
                'Authorization': f'Bearer {self.auth.access_token}'
            },
            params={
                'q': query
            }
        )
        discovery_response = response.json() if response and response.status_code == 200 else None
        if not discovery_response:
            return None
        next_token = discovery_response.get('nextRecordsUrl', None)
        accounts = discovery_response.get('records', None)
        
        return DiscoveryResponse(
            items=[Item(
                integration=self._INTEGRATION,
                id=account.get('Id', None) if account else None,
                title=account.get('Name', None) if account else None,
                icon=self.get_icon(),
                link=f'{BASE_URL}/{account.get("Id", None)}' if account else None,
            ) for account in accounts if account.get('Name', None) == 'YCombinator'],
            next_token=next_token
        )
    
    def _get_data(self, session: requests.Session, base_url: str, query: str) -> dict:
        response = session.get(base_url + '/services/data/v57.0/query', 
            params={
                'q': query
            }
        )
        return response.json() if response and response.status_code == 200 else None
    
    def _get_user_from_id(self, user_id_entity_map: Dict[str, entity], session: requests.Session, base_url: str, id: str, type: str = 'User') -> entity:
        if not id:
            return None
        if id in user_id_entity_map:
            return user_id_entity_map[id]
        query = f'SELECT Email, Name FROM {type} WHERE Id = \'{id}\''
        user_response = self._get_data(session, base_url, query)
        records = user_response.get('records', None) if user_response else None
        user = records[0] if records else None
        if not user:
            return None
        user_id = user.get('Email', None)
        user_name = user.get('Name', None)
        user_id_entity_map[id] = self._get_entity(id=user_id, name=user_name)
        return user_id_entity_map[id]
    
    # TODO: move to bulk read
    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('salesforce crm fetch!')

        succeeded = self.auth.refresh()
        if not succeeded:
            return None
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bearer {self.auth.access_token}'
        })
        query = f'SELECT Id, Name, Owner.Name, LastModifiedDate FROM Account WHERE Id = \'{id}\''
        account_response = self._get_data(session, BASE_URL, query)
        account = account_response.get('records', None)[0] if account_response else None
        if not account:
            return None
        user_id_entity_map: Dict[str, entity] = {}
        
        title_blocks: List[TitleBlock] = []
        account_last_updated_timestamp = self._get_timestamp_from_format(account.get('LastActivityDate', None))
        title_blocks.append(TitleBlock(
            last_updated_timestamp=account_last_updated_timestamp, 
            text=account.get('Name', None),
        ))
        yield from self._generate(TitleBlock._LABEL, title_blocks)

        comment_blocks: List[CommentBlock] = []
        query = f'SELECT OwnerId, Title, Body, LastModifiedDate FROM Note WHERE ParentId = \'{id}\''
        note_response = self._get_data(session, BASE_URL, query)
        notes = note_response.get('records', None) if note_response else None
        if notes:
            for note in notes:
                if not note:
                    continue

                author_id = note.get('OwnerId', {})
                author_entity = self._get_user_from_id(user_id_entity_map, session, BASE_URL, author_id)
                text = f'{note.get("Title", "")}: {note.get("Body", "")}'
                last_updated_timestamp = self._get_timestamp_from_format(note.get('LastModifiedDate', 'None'), '%Y-%m-%dT%H:%M:%S.%f%z')
                comment_blocks.append(CommentBlock(
                    last_updated_timestamp=last_updated_timestamp,
                    author=author_entity,
                    text=text,
                ))
        yield from self._generate(CommentBlock._LABEL, comment_blocks)

        contact_blocks: List[ContactBlock] = []
        query = f'SELECT Email, Name, OwnerId, Department, Title, LeadSource, LastReferencedDate FROM Contact WHERE AccountId = \'{id}\''
        contact_response = self._get_data(session, BASE_URL, query)
        contacts = contact_response.get('records', None) if contact_response else None
        if contacts:
            for contact in contacts:
                if not contact:
                    continue

                contact_email = contact.get('Email', None)
                contact_name = contact.get('Name', None)
                contact_entity = self._get_entity(id=contact_email, name=contact_name)
                created_by_id = contact.get('OwnerId', None)
                created_by_entity = self._get_user_from_id(user_id_entity_map, session, BASE_URL, created_by_id)
                contact_last_updated_timestamp = self._get_timestamp_from_format(contact.get('LastReferencedDate', None), '%Y-%m-%dT%H:%M:%S.%f%z')
                contact_blocks.append(ContactBlock(
                    last_updated_timestamp=contact_last_updated_timestamp,
                    name=contact_entity,
                    created_by=created_by_entity,
                    department=contact.get('Department', None),
                    title=contact.get('Title', None),
                    lead_source=contact.get('LeadSource', None),
                ))
        yield from self._generate(ContactBlock._LABEL, contact_blocks)

        deal_blocks: List[DealBlock] = []
        query = f'SELECT ContactId, Id, Name, Amount, CloseDate, StageName, OwnerId, Probability, Type, LastModifiedDate FROM Opportunity WHERE AccountId = \'{id}\''
        opportunity_response = self._get_data(session, BASE_URL, query)
        opportunities = opportunity_response.get('records', None) if opportunity_response else None
        if opportunities:
            for opportunity in opportunities:
                if not opportunity:
                    continue

                owner_id = opportunity.get('OwnerId', None)
                owner_entity = self._get_user_from_id(user_id_entity_map, session, BASE_URL, owner_id)
                contact_id = opportunity.get('ContactId', None)
                contact_entity = self._get_user_from_id(user_id_entity_map, session, BASE_URL, contact_id, 'Contact')
                deal_id = opportunity.get('Id', None)
                deal_name = opportunity.get('Name', None)
                deal_entity = self._get_entity(deal_id, deal_name)
                deal_last_updated_timestamp = self._get_timestamp_from_format(opportunity.get('LastModifiedDate', None), '%Y-%m-%dT%H:%M:%S.%f%z')
                deal_blocks.append(DealBlock(
                    last_updated_timestamp=deal_last_updated_timestamp,
                    owner=owner_entity,
                    name=deal_entity,
                    contact=contact_entity,
                    type=opportunity.get('Type', None),
                    stage=opportunity.get('StageName', None),
                    close_date=opportunity.get('CloseDate', None),
                    amount=opportunity.get('Amount', None),
                    probability=opportunity.get('Probability', None),
                ))
        yield from self._generate(DealBlock._LABEL, deal_blocks)
