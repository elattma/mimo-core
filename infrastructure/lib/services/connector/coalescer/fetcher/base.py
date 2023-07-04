from abc import ABC, abstractmethod
from typing import Dict, Generator, List

from auth.base import AuthStrategy, AuthType
from fetcher.model import Filter, StreamData


class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}
    _filter: Filter = None
    _auth_strategy: AuthStrategy = None
    _config: Dict = None
    _requester = None

    @classmethod
    def create(cls, 
               integration: str,
               auth_strategy: AuthStrategy,
               config: Dict = None,
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
        if fetcher._get_supported_auth_types():
            if not (auth_strategy and auth_strategy.get_type() in fetcher._get_supported_auth_types()):
                raise Exception(f'Fetcher.create() invalid auth_strategy.. {auth_strategy}')
        fetcher._auth_strategy = auth_strategy
        fetcher._config = config
        fetcher._filter = Filter(
            start_timestamp=last_ingested_at,
            limit=limit
        )
        print(f'Fetcher.create() {fetcher._INTEGRATION} {fetcher._config} {fetcher._filter}')
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
                print(auth)
                authorization = f'Bearer {auth.access_token}'
            elif self._auth_strategy.get_type() == AuthType.BASIC:
                auth: Basic = self._auth_strategy._auth
                authorization = f'Basic {auth.key}'
            self._requester.headers.update({
                'Authorization': authorization
            })
        if self._auth_strategy.get_type() == AuthType.TOKEN_OAUTH2:
            auth: TokenOAuth2 = self._auth_strategy._auth
            if auth.refresh_token and auth.expiry_timestamp < int(time()) + 300:
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
    def discover(self) -> Generator[StreamData, None, None]:
        raise NotImplementedError('discover not implemented')

    @abstractmethod
    def fetch(self, stream: StreamData) -> None:
        raise NotImplementedError("fetch not implemented")
