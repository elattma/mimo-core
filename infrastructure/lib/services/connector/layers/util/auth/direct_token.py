from dataclasses import dataclass

from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class TokenDirect(Auth):
    access_token: str

    def is_valid(self):
        return self.timestamp and self.access_token
    
    def as_dict(self):
        return {
            'type': AuthType.TOKEN_DIRECT.value,
            'timestamp': self.timestamp,
            'access_token': self.access_token
        }

@dataclass
class TokenDirectStrategy(AuthStrategy):
    id: str
    
    @classmethod
    def get_type(cls) -> AuthType:
        return AuthType.TOKEN_DIRECT
    
    def get_params(self):
        return {}
    
    @classmethod
    def auth_from_params(cls, timestamp: int, access_token: str) -> TokenDirect:
        # validate with api
        return TokenDirect(timestamp=timestamp, access_token=access_token)
    
    def auth(self, timestamp: int, access_token: str) -> TokenDirect:
        # validate with api
        return TokenDirect(timestamp=timestamp, access_token=access_token)
    