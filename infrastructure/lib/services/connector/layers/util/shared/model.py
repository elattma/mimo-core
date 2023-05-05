from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List


class AuthType(Enum):
    TOKEN_OAUTH2 = 'token_oauth2'
    TOKEN_DIRECT = 'token_direct'

@dataclass
class AuthStrategy(ABC):
    subclasses = {}

    @classmethod
    def create(cls, type: AuthType, **kwargs) -> 'AuthStrategy':
        if not cls.subclasses:
            cls.subclasses = {
                subclass.get_type(): subclass for subclass in cls.__subclasses__()
            }

        if not cls.subclasses.get(type, None):
            print(f'auth strategy not found for {type}')
            return None

        return cls.subclasses[type](**kwargs)

    @classmethod
    @abstractmethod
    def get_type(cls) -> AuthType:
        raise Exception('get_type() not implemented')
    
    @abstractmethod
    def get_params(self):
        raise Exception('get_params() not implemented')
    
@dataclass
class TokenOAuth2Strategy(AuthStrategy):
    oauth2_link: str
    authorize_endpoint: str
    client_id: str
    client_secret: str
    refresh_endpoint: str = None

    @classmethod
    def get_type(cls) -> AuthType:
        return AuthType.TOKEN_OAUTH2
    
    def get_params(self):
        return {
            'oauth2_link': self.oauth2_link,
        }

@dataclass
class Integration:
    id: str
    name: str
    description: str
    icon: str
    auth_strategies: Dict[AuthType, AuthStrategy]

    @staticmethod
    def from_dict(params: Dict[str, Any]) -> 'Integration':
        id: str = params.get('id', None)
        name: str = params.get('name', None)
        description: str = params.get('description', None)
        icon: str = params.get('icon', None)
        if not (id and name and description and icon):
            print('Integration.from_dict() missing required params for:', id)
            return None

        auth_strategies_dict: Dict[str, Dict[str]] = params.get('auth_strategies', None)
        auth_strategies: Dict[AuthType, AuthStrategy] = {}
        for type, strategy in auth_strategies_dict.items():
            auth_type = AuthType(type)
            auth_strategy = AuthStrategy.create(auth_type, **strategy)
            auth_strategies[auth_type] = auth_strategy
            
        return Integration(
            id=id,
            name=name,
            description=description,
            icon=icon,
            auth_strategies=auth_strategies
        )

@dataclass
class Auth(ABC):
    subclasses = {}
    type: AuthType

    @classmethod
    def create(cls, type: str, **kwargs) -> 'Auth':
        if not cls.subclasses:
            cls.subclasses = {}
            for subclass in cls.__subclasses__():
                for type in subclass.get_possible_types():
                    cls.subclasses[type] = subclass

        if not cls.subclasses.get(type, None):
            print(f'auth not found for {type}')
            return None

        return cls.subclasses[type](**kwargs)

    @classmethod
    @abstractmethod
    def get_possible_types(cls) -> List[AuthType]:
        raise Exception('get_possible_types() not implemented')

    @abstractmethod
    def is_valid(self):
        pass

    def __str__(self):
        return f'Auth(type={self.type})'

@dataclass
class TokenAuth(Auth):
    access_token: str
    refresh_token: str = None
    timestamp: int = None
    expiry_timestamp: int = None

    @classmethod
    def get_possible_types(cls) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT]

    def is_valid(self):
        return self.access_token or self.refresh_token

@dataclass
class Connection:
    id: str = None
    name: str = None
    integration: str = None
    auth: Auth = None
    created_at: int = None
    ingested_at: int = None
    
    def is_valid(self):
        return self.id and self.name and self.integration \
            and self.auth and self.auth.is_valid() and self.created_at
    
@dataclass
class Library:
    id: str = None
    name: str = None
    created_at: int = None

    def is_valid(self):
        return self.id and self.name and self.created_at