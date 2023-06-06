from time import time

from shared.model import SyncStatus
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB


class SyncState:
    _db: ParentChildDB = None
    
    def __init__(self, db: ParentChildDB, library_id: str, connection_id: str):
        self._db = db
        item: LibraryConnectionItem = self._db.get(
            f'{KeyNamespaces.LIBRARY.value}{library_id}',
            f'{KeyNamespaces.CONNECTION.value}{connection_id}',
            ConsistentRead=True
        )
        if not (item and item.connection and item.connection.is_valid()):
            raise Exception('Failed to find connection!')
        self._library = library_id
        self._connection = item.connection

    def is_locked(self) -> bool:
        if not self._connection.sync:
            return False
        return self._connection.sync.status == SyncStatus.IN_PROGRESS
    
    def hold_lock(self) -> bool:
        if self.is_locked():
            print('lock is already held!', str(self._connection))
            return False
        
        return self.checkpoint(SyncStatus.IN_PROGRESS)
    
    def release_lock(self, succeeded: bool) -> bool:
        return self.checkpoint(SyncStatus.SUCCESS if succeeded else SyncStatus.FAILED)
 
    def checkpoint(self, sync_status: SyncStatus) -> bool:
        now_timestamp = int(time())
        return self._db.update(
            f'{KeyNamespaces.LIBRARY.value}{self._library}',
            f'{KeyNamespaces.CONNECTION.value}{self._connection.id}',
            {
                'sync': {
                    'status': sync_status.value,
                    'checkpoint_at': now_timestamp,
                    'ingested_at': now_timestamp if sync_status == SyncStatus.SUCCESS else self._connection.sync.ingested_at
                }
            }
        )
