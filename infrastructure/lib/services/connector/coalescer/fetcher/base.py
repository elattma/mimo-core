from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Generator, List

from auth.base import AuthStrategy, AuthType
from dstruct.model import Discovery


def get_timestamp_from_format(timestamp_str: str, format: str = None) -> int:
    if not (timestamp_str and format):
        return None
    timestamp_datetime = datetime.strptime(timestamp_str, format)
    return int(timestamp_datetime.timestamp())

@dataclass
class Filter:
    start_timestamp: int = None
    limit: int = None
    
class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}
    _filter: Filter = None
    _auth_strategy: AuthStrategy = None
    _requester = None

    @classmethod
    def create(cls, 
               integration: str,
               auth_strategy: AuthStrategy,
               last_ingested_at: int = None, 
               limit: int = None) -> 'Fetcher':    
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }
        subclass = cls.subclasses.get(integration, None)

        if not (integration and subclass):
            raise Exception(f'Fetcher.create() invalid integration.. {integration}')

        fetcher = subclass()
        if not (auth_strategy and auth_strategy.get_type() in fetcher._get_supported_auth_types()):
            raise Exception(f'Fetcher.create() invalid auth_strategy.. {auth_strategy}')
        fetcher._auth_strategy = auth_strategy
        fetcher._filter = Filter(
            start_timestamp=last_ingested_at,
            limit=limit
        )
        return fetcher
    
    def request(self, url: str, method: str = 'get', **kwargs) -> Dict:
        from time import time

        import requests
        from auth.basic import Basic
        from auth.direct_token import TokenDirect
        from auth.oauth2_token import TokenOAuth2

        if not self._requester:
            self._requester = requests.Session()
            authorization: str = None
            if self._auth_strategy.get_type() == AuthType.TOKEN_DIRECT:
                auth: TokenDirect = self._auth_strategy._auth
                authorization = f'Bearer {auth.access_token}'
            elif self._auth_strategy.get_type() == AuthType.TOKEN_OAUTH2:
                auth: TokenOAuth2 = self._auth_strategy._auth
                authorization = f'Bearer {auth.access_token}'
            elif self._auth_strategy.get_type() == AuthType.BASIC:
                auth: Basic = self._auth_strategy._auth
                authorization = f'Basic {auth.key}'
            self._requester.headers.update({
                'Authorization': authorization
            })
        if self._auth_strategy.get_type() == AuthType.TOKEN_OAUTH2:
            auth: TokenOAuth2 = self._auth_strategy._auth
            if auth.expiry_timestamp < int(time()) + 300:
                auth = self._auth_strategy.auth()
                self._requester.headers.update({
                    'Authorization': f'Bearer {auth.access_token}'
                })
        response = self._requester.request(url=url, method=method, **kwargs)
        return response.json() if response else None
    
    @abstractmethod
    def _get_supported_auth_types(self) -> List[AuthType]:
        raise NotImplementedError('_get_supported_auth_types not implemented')
    
    @abstractmethod
    def discover(self) -> Generator[Discovery, None, None]:
        raise NotImplementedError('discover not implemented')

    @abstractmethod
    def fetch(self, discovery: Discovery) -> None:
        raise NotImplementedError("fetch not implemented")
