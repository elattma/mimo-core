from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict

from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class Integration:
    id: str
    name: str
    description: str
    icon: str
    airbyte_id: str
    auth_strategies: Dict[AuthType, AuthStrategy]

    @staticmethod
    def from_dict(params: Dict[str, Any]) -> 'Integration':
        id: str = params.get('id', None)
        name: str = params.get('name', None)
        description: str = params.get('description', None)
        icon: str = params.get('icon', None)
        airbyte_id: str = params.get('airbyte_id', None)
        if not (id and name and description and icon and airbyte_id):
            print('Integration.from_dict() missing required params for:', id)
            return None

        auth_strategies_dict: Dict[str, Dict[str]] = params.get('auth_strategies', {})
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
            airbyte_id=airbyte_id,
            auth_strategies=auth_strategies
        )
    
class SyncStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    UNSYNCED = "UNSYNCED"
    IN_PROGRESS = "IN_PROGRESS"

@dataclass
class Sync:
    status: SyncStatus
    checkpoint_at: int
    ingested_at: int

    @staticmethod
    def from_dict(item: dict) -> 'Sync':
        if not item:
            return None

        status = item.get('status', None)
        checkpoint_at = item.get('checkpoint_at', None)
        ingested_at = item.get('ingested_at', None)

        return Sync(
            status=SyncStatus(status) if status else None,
            checkpoint_at=int(checkpoint_at) if checkpoint_at else None,
            ingested_at=int(ingested_at) if ingested_at else None,
        )
    
    def as_dict(self) -> dict:
        return {
            'status': self.status.value,
            'checkpoint_at': self.checkpoint_at,
            'ingested_at': self.ingested_at,
        }

@dataclass
class Connection:
    id: str = None
    name: str = None
    integration: str = None
    auth: Auth = None
    created_at: int = None
    sync: Sync = None
    
    def is_valid(self):
        return self.id and self.name and self.integration and self.auth \
            and self.auth.is_valid() and self.created_at
    
@dataclass
class Library:
    id: str = None
    name: str = None
    created_at: int = None

    def is_valid(self):
        return self.id and self.name and self.created_at