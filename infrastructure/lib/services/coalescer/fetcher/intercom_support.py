from typing import Any, Generator, List, Set

import requests
from model.blocks import (BlockStream, BodyBlock, CommentBlock, MemberBlock,
                          Relations, TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item


class IntercomSupport(Fetcher):
    _INTEGRATION = 'intercom_support'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('intercom discovery!')

        session = requests.Session()
        

    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        print('intercom fetch!')

        session = requests.Session()
        session.headers.update({
            'Authorization': 'Bearer dG9rOmVkMmZiMzAyXzc5ZGZfNDRkMl9iN2Y3X2I0MjFlNTZiOGQ2YjoxOjA='
        })
