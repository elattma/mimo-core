from datetime import datetime
from typing import Generator, List
from urllib.parse import quote

import requests
from graph.blocks import (Block, CommentBlock, ContactBlock, DealBlock,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item


class SalesforceCrm(Fetcher):
    _INTEGRATION = 'salesforce_crm'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
            'authorize_endpoint': 'https://mimo2-dev-ed.develop.my.salesforce.com/services/oauth2/token',
            'refresh_endpoint': 'https://mimo2-dev-ed.develop.my.salesforce.com/services/oauth2/token',
        }
    
    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('salesforce crm discovery!')

        succeeded = self.auth.refresh()
        if not succeeded:
            return None
        
    # TODO: move to bulk read
    def fetch(self, id: str) -> Generator[Block, None, None]:
        print('salesforce crm fetch!')

        succeeded = self.auth.refresh()