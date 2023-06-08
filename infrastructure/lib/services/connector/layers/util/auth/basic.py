from dataclasses import dataclass

from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class Basic(Auth):
    user: str
    password: str

    def is_valid(self):
        return self.timestamp and self.user and self.password

    def as_dict(self):
        return {
            'type': AuthType.BASIC.value,
            'timestamp': self.timestamp,
            'user': self.user,
            'password': self.password
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
    def auth_from_params(cls, timestamp: int, user: str, password: str) -> Basic:
        # validate with api
        return Basic(timestamp=timestamp, user=user, password=password)
    
    def auth(self, timestamp: int, user: str, password: str) -> Basic:
        # validate with api
        self._auth = Basic(timestamp=timestamp, user=user, password=password)
        return self._auth
