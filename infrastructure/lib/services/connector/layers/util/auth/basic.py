from dataclasses import dataclass

from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class Basic(Auth):
    key: str

    def is_valid(self):
        return self.timestamp and self.key

    def as_dict(self):
        return {
            'type': AuthType.BASIC.value,
            'timestamp': self.timestamp,
            'key': self.key
        }

@dataclass
class BasicStrategy(AuthStrategy):
    id: str

    @classmethod
    def get_type(cls) -> AuthType:
        return AuthType.BASIC

    def get_params(self):
        return {}
    
    @classmethod
    def auth_from_params(cls, timestamp: int, key: str) -> Basic:
        # validate with api
        return Basic(timestamp=timestamp, key=key)
    
    def auth(self, timestamp: int, key: str) -> Basic:
        # validate with api
        self._auth = Basic(timestamp=timestamp, key=key)
        return self._auth
