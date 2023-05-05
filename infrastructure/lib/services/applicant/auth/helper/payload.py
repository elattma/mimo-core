from dataclasses import dataclass


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