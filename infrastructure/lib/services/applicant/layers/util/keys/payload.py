from dataclasses import dataclass
from typing import Dict


@dataclass
class AppPayload:
    id: str
    name: str

@dataclass
class Payload:
    app: AppPayload
    user: str
    timestamp: int
    expiration: int

    def to_dict(self):
        return {
            'app': {
                'id': self.app.id,
                'name': self.app.name
            },
            'user': self.user,
            'timestamp': self.timestamp,
            'expiration': self.expiration
        }
    
    @staticmethod
    def from_dict(item: dict):
        if not item:
            return None
        
        app: Dict = item.get('app', None)
        user = item.get('user', None)
        timestamp = item.get('timestamp', None)
        expiration = item.get('expiration', None)
        if not (app and user and timestamp and expiration):
            return None
        
        app_id = app.get('id', None)
        app_name = app.get('name', None)
        if not (app_id and app_name):
            return None
        
        return Payload(
            app=AppPayload(
                id=app_id,
                name=app_name
            ),
            user=user,
            timestamp=int(timestamp),
            expiration=int(expiration)
        )
    