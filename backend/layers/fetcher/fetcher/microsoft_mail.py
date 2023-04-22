import base64
from typing import Generator, List, Set

import requests
from graph.blocks import (BlockStream, BodyBlock, MemberBlock, Relations,
                          TitleBlock, entity)

from .base import DiscoveryResponse, Fetcher, Filter, Item


class MicrosoftMail(Fetcher):
    _INTEGRATION = 'microsoft_mail'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
        }

    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        print('microsoft_mail discovery!')

    def fetch(self, id: str) -> Generator[BlockStream, None, None]:
        print('microsoft_mail load!')
