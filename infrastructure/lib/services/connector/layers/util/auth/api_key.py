from dataclasses import dataclass

from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class ApiKey(Auth):
    key: str

    def is_valid(self):
        return self.timestamp and self.key

    def as_dict(self):
        return {
            'type': AuthType.API_KEY.value,
            'timestamp': self.timestamp,
            'key': self.key
        }

@dataclass
class ApiKeyStrategy(AuthStrategy):
    id: str

    @classmethod
    def get_type(cls) -> AuthType:
        return AuthType.API_KEY

    def get_params(self):
        return {}
    
    @classmethod
    def auth_from_params(cls, timestamp: int, key: str) -> ApiKey:
        # validate with api
        return ApiKey(timestamp=timestamp, key=key)
    
    def auth(self, timestamp: int, key: str) -> ApiKey:
        # validate with api
        self._auth = ApiKey(timestamp=timestamp, key=key)
        return self._auth
