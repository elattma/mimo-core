from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Generator, List

import requests


def get_timestamp_from_format(timestamp_str: str, format: str = None) -> int:
    if not (timestamp_str and format):
        return None
    timestamp_datetime = datetime.strptime(timestamp_str, format)
    return int(timestamp_datetime.timestamp())

@dataclass
class Filter:
    start_timestamp: int = None
    limit: int = None

@dataclass
class Discovery:
    id: str
    type: str

@dataclass
class Section(ABC):
    discovery: Discovery
    last_updated_timestamp: int

    @classmethod
    @abstractmethod
    def headers(cls) -> List[str]:
        raise NotImplementedError('headers not implemented')

    @abstractmethod
    def row(self) -> List[Any]:
        raise NotImplementedError('row not implemented')
    
class Fetcher(ABC):
    _INTEGRATION = 'base'

    subclasses = {}
    _request_session: requests.Session = None
    _filter: Filter = None

    @classmethod
    def create(cls, 
               integration: str, 
               access_token: str = None, 
               last_ingested_at: int = None, 
               limit: int = None) -> 'Fetcher':    
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }
        subclass = cls.subclasses.get(integration, None)

        if not (integration and access_token and subclass):
            print(f'Fetcher.create() invalid connection.. {integration}')
            return None

        fetcher = subclass()
        fetcher._filter = Filter(
            start_timestamp=last_ingested_at,
            limit=limit
        )
        if access_token:
            fetcher._request_session = requests.session()
            fetcher._request_session.headers.update({
                'Authorization': f'Bearer {access_token}'
            })
            print(access_token)
        return fetcher
    
    @abstractmethod
    def discover(self) -> Generator[Discovery, None, None]:
        raise NotImplementedError('discover not implemented')

    @abstractmethod
    def fetch(self, discovery: Discovery) -> List[Section]:
        raise NotImplementedError("fetch not implemented")
