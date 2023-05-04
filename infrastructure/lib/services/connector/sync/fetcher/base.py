from abc import ABC, abstractmethod
from typing import Generator

import requests
from model import Filter, Page, Section
from shared.model import Connection, TokenAuth


class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}
    _request_session: requests.Session = None
    _filter: Filter = None

    @classmethod
    def create(cls, connection: Connection) -> 'Fetcher':    
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }
        integration = connection.integration
        auth = connection.auth
        subclass = cls.subclasses.get(integration, None)

        if not (integration and auth and subclass):
            print(f'Fetcher.create() invalid connection.. {integration}, {auth}')
            return None

        fetcher = subclass()
        fetcher._filter = Filter(start_timestamp=connection.ingested_at)
        if isinstance(auth, TokenAuth):
            fetcher.token_auth(auth, filter)
        return fetcher
    
    def token_auth(self, auth: TokenAuth):
        self._request_session = requests.session()
        self._request_session.headers.update({
            'Authorization': f'Bearer {auth.access_token}'
        })
    
    @abstractmethod
    def discover(self, filter: Filter = None) -> Generator[Page, None, None]:
        raise NotImplementedError('discover not implemented')

    @abstractmethod
    def fetch(self, page: Page) -> Generator[Section, None, None]:
        raise NotImplementedError("fetch not implemented")
