from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class AuthType(Enum):
    TOKEN_OAUTH2 = 'token_oauth2'
    TOKEN_DIRECT = 'token_direct'
    BASIC = 'basic'
    API_KEY = 'api_key'

@dataclass
class Auth(ABC):
    timestamp: int

    @abstractmethod
    def is_valid(self) -> bool:
        raise NotImplementedError('is_valid not implemented')

    @abstractmethod
    def as_dict(self) -> Dict:
        raise NotImplementedError('as_dict not implemented')

class AuthStrategy(ABC):
    subclasses = {}
    _auth: Auth = None

    @classmethod
    def init_subclasses(cls, type: AuthType):
        if not cls.subclasses:
            cls.subclasses = {
                subclass.get_type(): subclass for subclass in cls.__subclasses__()
            }
        if not cls.subclasses.get(type, None):
            raise Exception(f'auth strategy not found for {type}')

    @classmethod
    def create(cls, type: AuthType, **kwargs) -> 'AuthStrategy':
        cls.init_subclasses(type)
        return cls.subclasses[type](**kwargs)
    
    @classmethod
    @abstractmethod
    def get_type(cls) -> AuthType:
        raise Exception('get_type() not implemented')

    @abstractmethod
    def get_params(self):
        raise Exception('get_params() not implemented')
    
    @classmethod
    def auth_from_params(cls, type: AuthType, **kwargs) -> Auth:
        cls.init_subclasses(type)
        return cls.subclasses[type].auth_from_params(**kwargs)
    
    @abstractmethod
    def auth(self, **kwargs) -> Auth:
        raise Exception('auth() not implemented')
