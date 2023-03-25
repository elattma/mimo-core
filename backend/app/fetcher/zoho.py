from typing import Generator

import requests
from app.fetcher.base import Block, DiscoveryResponse, Fetcher, Filter, Item


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

        filters = {}
        if filter:
            if filter.next_token:
                filters['page'] = filter.next_token
            if filter.limit:
                filters['per_page'] = filter.limit

        succeeded = self.auth.refresh()
        if not succeeded:
            print('failed to refresh google mail token')
            return None
        
        response = requests.get(
            'https://www.zohoapis.com/crm/v2/Accounts/search',
            params={ **filters },
            headers={
                'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
            }
        )
        discovery_response = response.json()
        accounts = discovery_response.get('data', None) if discovery_response else None

        response = requests.get(
            'https://www.zohoapis.com/crm/v2/org',
            headers={
                'Authorization': f'Zoho-oauthtoken {self.auth.access_token}'
            }
        )
        org_response = response.json()
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
            ) for account in accounts],
            next_token=filter.next_token + 1 if filter and filter.next_token else 2
        )

    def fetch(self, id: str) -> Generator[Block, None, None]:
        pass