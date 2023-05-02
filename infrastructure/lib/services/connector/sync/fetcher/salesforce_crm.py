from typing import Dict, Generator, List

from model.blocks import (BlockStream, CommentBlock, ContactBlock, DealBlock,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter
from .model import IntegrationTypes, Page, PageTypes
from .util import generate, get_entity, get_timestamp_from_format

BASE_URL = 'https://mimo2-dev-ed.develop.my.salesforce.com'

class SalesforceCrm(Fetcher):
    _INTEGRATION = 'salesforce_crm'

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('salesforce crm discovery!')
        
        suffix = '/services/data/v57.0/query'
        limit = 100
        if filter:
            if filter.next_token:
                suffix = filter.next_token
            if filter.limit:
                limit = filter.limit
        query = f'SELECT Id, Name FROM Account LIMIT {limit}'
        response = self._request_session.get(f'{BASE_URL}{suffix}', params={'q': query})
        discovery_response: Dict = response.json() if response and response.status_code == 200 else None
        if not discovery_response:
            return None
        next_token = discovery_response.get('nextRecordsUrl', None)
        accounts: List[Dict] = discovery_response.get('records', None)
        
        return DiscoveryResponse(
            integration_type=IntegrationTypes.CRM,
            pages=[Page(
                type=PageTypes.ACCOUNT,
                id=account.get('Id', None) if account else None
            ) for account in accounts if account],
            next_token=next_token
        )
    
    def _get_user_from_id(self, user_id_entity_map: Dict[str, entity], id: str, type: str = 'User') -> entity:
        if not id:
            return None
        if id in user_id_entity_map:
            return user_id_entity_map[id]
        query = f'SELECT Email, Name FROM {type} WHERE Id = \'{id}\''
        response = self._request_session.get(f'{BASE_URL}/services/data/v57.0/query', params={'q': query})
        user_response: Dict = response.json() if response and response.status_code == 200 else None
        records: Dict = user_response.get('records', None) if user_response else None
        user: Dict = records[0] if records else None
        if not user:
            return None
        user_id = user.get('Email', None)
        user_name = user.get('Name', None)
        user_id_entity_map[id] = get_entity(id=user_id, name=user_name)
        return user_id_entity_map[id]
    
    def _generate_title(self, account: Dict) -> Generator[BlockStream, None, None]:
        account_lut = get_timestamp_from_format(account.get('LastModifiedDate', None))
        title_blocks: List[TitleBlock] = []
        title_blocks.append(TitleBlock(
            last_updated_timestamp=account_lut, 
            text=account.get('Name', None),
        ))
        yield from generate(TitleBlock._LABEL, title_blocks)

    def _generate_comment(self, response: Dict, user_id_entity_map: Dict[str, entity]) -> Generator[BlockStream, None, None]:
        notes = response.get('records', None) if response else None
        comment_blocks: List[CommentBlock] = []
        if notes:
            for note in notes:
                if not note:
                    continue

                author_id = note.get('OwnerId', {})
                author_entity = self._get_user_from_id(user_id_entity_map, author_id)
                text = f'{note.get("Title", "")}: {note.get("Body", "")}'
                last_updated_timestamp = get_timestamp_from_format(note.get('LastModifiedDate', 'None'), '%Y-%m-%dT%H:%M:%S.%f%z')
                comment_blocks.append(CommentBlock(
                    last_updated_timestamp=last_updated_timestamp,
                    author=author_entity,
                    text=text,
                ))
        yield from generate(CommentBlock._LABEL, comment_blocks)

    def _generate_contact(self, response: Dict, user_id_entity_map: Dict[str, entity]) -> Generator[BlockStream, None, None]:
        contacts = response.get('records', None) if response else None
        contact_blocks: List[ContactBlock] = []
        if contacts:
            for contact in contacts:
                if not contact:
                    continue

                contact_email = contact.get('Email', None)
                contact_name = contact.get('Name', None)
                contact_entity = get_entity(id=contact_email, name=contact_name)
                created_by_id = contact.get('OwnerId', None)
                created_by_entity = self._get_user_from_id(user_id_entity_map, created_by_id)
                contact_last_updated_timestamp = get_timestamp_from_format(contact.get('LastReferencedDate', None), '%Y-%m-%dT%H:%M:%S.%f%z')
                contact_blocks.append(ContactBlock(
                    last_updated_timestamp=contact_last_updated_timestamp,
                    name=contact_entity,
                    created_by=created_by_entity,
                    department=contact.get('Department', None),
                    title=contact.get('Title', None),
                    lead_source=contact.get('LeadSource', None),
                ))
        yield from generate(ContactBlock._LABEL, contact_blocks)

    def _generate_deal(self, response: Dict, user_id_entity_map: Dict[str, entity]) -> Generator[BlockStream, None, None]:
        deals: List[Dict] = response.get('records', None) if response else None
        deal_blocks: List[DealBlock] = []
        if deals:
            for deal in deals:
                if not deal:
                    continue

                owner_id = deal.get('OwnerId', None)
                owner_entity = self._get_user_from_id(user_id_entity_map, owner_id)
                contact_id = deal.get('ContactId', None)
                contact_entity = self._get_user_from_id(user_id_entity_map, contact_id, 'Contact')
                deal_id = deal.get('Id', None)
                deal_name = deal.get('Name', None)
                deal_entity = get_entity(deal_id, deal_name)
                deal_last_updated_timestamp = get_timestamp_from_format(deal.get('LastModifiedDate', None), '%Y-%m-%dT%H:%M:%S.%f%z')
                deal_blocks.append(DealBlock(
                    last_updated_timestamp=deal_last_updated_timestamp,
                    owner=owner_entity,
                    name=deal_entity,
                    contact=contact_entity,
                    type=deal.get('Type', None),
                    stage=deal.get('StageName', None),
                    close_date=deal.get('CloseDate', None),
                    amount=deal.get('Amount', None),
                    probability=deal.get('Probability', None),
                ))
        yield from generate(DealBlock._LABEL, deal_blocks)
    
    def fetch(self, page: Page) -> Generator[BlockStream, None, None]:
        print('salesforce crm fetch!')

        query = f'SELECT Id, Name, Owner.Name, LastModifiedDate FROM Account WHERE Id = \'{page.id}\''
        response = self._request_session.get(f'{BASE_URL}/services/data/v57.0/query', params={'q': query})
        account_response: Dict = response.json() if response and response.status_code == 200 else None
        account: Dict = account_response.get('records', None)[0] if account_response else None
        if not account:
            return
        yield from self._generate_title(account)

        user_id_entity_map: Dict[str, entity] = {}
        query = f'SELECT OwnerId, Title, Body, LastModifiedDate FROM Note WHERE ParentId = \'{id}\''
        response = self._request_session.get(f'{BASE_URL}/services/data/v57.0/query', params={'q': query})
        note_response: Dict = response.json() if response and response.status_code == 200 else None
        yield from self._generate_comment(note_response, user_id_entity_map)
        
        query = f'SELECT Email, Name, OwnerId, Department, Title, LeadSource, LastReferencedDate FROM Contact WHERE AccountId = \'{id}\''
        response = self._request_session.get(f'{BASE_URL}/services/data/v57.0/query', params={'q': query})
        contact_response: Dict = response.json() if response and response.status_code == 200 else None
        yield from self._generate_contact(contact_response, user_id_entity_map)

        query = f'SELECT ContactId, Id, Name, Amount, CloseDate, StageName, OwnerId, Probability, Type, LastModifiedDate FROM Opportunity WHERE AccountId = \'{id}\''
        response = self._request_session.get(f'{BASE_URL}/services/data/v57.0/query', params={'q': query})
        opportunity_response = response.json() if response and response.status_code == 200 else None
        yield from self._generate_deal(opportunity_response, user_id_entity_map)
