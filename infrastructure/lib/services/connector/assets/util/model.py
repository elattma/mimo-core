from abc import ABC
from dataclasses import dataclass
from enum import Enum


@dataclass
class Integration:
    id: str = ''
    name: str = ''
    description: str = ''
    icon: str = ''
    oauth2_link: str = ''

class AuthType(Enum):
    TOKEN_OAUTH2 = 'TOKEN_OAUTH2'

@dataclass
class Auth(ABC):
    type: AuthType

@dataclass
class TokenOAuth2(Auth):
    access_token: str
    refresh_token: str
    timestamp: int
    expiry_timestamp: int

@dataclass
class Connection:
    id: str = None
    name: str = None
    integration: str = None
    auth: Auth = None
    created_at: int = None
    ingested_at: int = None

    def to_response(self):
        return {
            'id': self.id,
            'name': self.name,
            'integration': self.integration,
            'created_at': self.created_at,
            'ingested_at': self.ingested_at,
        }