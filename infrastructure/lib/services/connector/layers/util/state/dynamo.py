from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from shared.model import Auth, AuthType, Connection, Library, SyncStatus


class KeyNamespaces(Enum):
    USER = "USER#"
    LIBRARY = "LIBRARY#"
    CONNECTION = "CONNECTION#"

@dataclass
class ParentChildItem(ABC):
    parent: str

    def get_raw_parent(self):
        if not self.parent:
            return None
        return self.parent.split('#')[-1]
    
    @abstractmethod
    def get_raw_child(self):
        pass

    @abstractmethod
    def get_child(self):
        pass

    @abstractmethod
    def is_valid(self):
        pass

    @abstractmethod
    def as_dict(self):
        pass

@dataclass
class UserLibraryItem(ParentChildItem):
    library: Library = None

    def get_raw_child(self):
        return self.library.id if self.library else None

    def get_child(self):
        return KeyNamespaces.LIBRARY.value + self.library.id if self.library else None

    def is_valid(self):
        return self.parent and self.library and self.library.is_valid()

    def as_dict(self):
        if not self.is_valid():
            return None
        
        return {
            'parent': self.parent,
            'child': self.get_child(),
            'name': self.library.name,
            'created_at': self.library.created_at
        }
    
    @staticmethod
    def from_dict(item: dict):
        if not item:
            return None

        parent: str = item.get('parent', None)
        child: str = item.get('child', None)
        if not (parent and child):
            return None
        
        name = item.get('name', None)
        created_at = item.get('created_at', None)
        library = Library(
            id=child.split('#')[-1],
            name=name,
            created_at=int(created_at) if created_at else None,
        )

        return UserLibraryItem(
            parent=parent,
            library=library,
        )

@dataclass
class LibraryConnectionItem(ParentChildItem):
    connection: Connection = None

    def get_raw_child(self):
        return self.connection.id if self.connection else None
    
    def get_child(self):
        return KeyNamespaces.CONNECTION.value + self.connection.id if self.connection else None
    
    def is_valid(self):
        return self.parent and self.connection and self.connection.is_valid()

    def as_dict(self):
        if not self.is_valid():
            return None
        
        return {
            'parent': self.parent,
            'child': self.get_child(),
            'name': self.connection.name,
            'integration': self.connection.integration,
            'auth': self.connection.auth.as_dict() if self.connection.auth else None,
            'created_at': self.connection.created_at,
            'ingested_at': self.connection.ingested_at,
        }

    @staticmethod
    def from_dict(item: dict):
        if not item:
            return None

        parent: str = item.get('parent', None)
        child: str = item.get('child', None)
        if not (parent and child):
            return None
        
        auth: dict = item.get('auth', None)
        auth_type = auth.get('type', None) if auth else None
        auth_type: AuthType = AuthType(auth_type) if auth_type else None
        auth.pop('type', None)
        auth = Auth.create(auth_type, **auth) if auth else None
        
        name = item.get('name', None)
        integration = item.get('integration', None)
        created_at = item.get('created_at', None)
        ingested_at = item.get('ingested_at', None)
        sync_status = item.get('sync_status', None)
        connection = Connection(
            id=child.split('#')[-1],
            name=name,
            integration=integration,
            auth=auth,
            created_at=int(created_at) if created_at else None,
            ingested_at=int(ingested_at) if ingested_at else None,
            sync_status=SyncStatus(sync_status) if sync_status else None,
        )

        return LibraryConnectionItem(
            parent=parent,
            connection=connection,
        )
    
class ParentChildDB:
    table = None
    def __init__(self, table_name: str):
        if not self.table:
            self.table = boto3.resource('dynamodb').Table(table_name)
            self.table.load()
        
    def write(self, items: List[ParentChildItem]) -> None:
        try:
            with self.table.batch_writer() as writer:
                for item in items:
                    writer.put_item(Item=item.as_dict())
        except ClientError as err:
            print("Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def update(self, parent: str, child: str, kv_update_map: Dict, **kwargs) -> Dict:
        if not kv_update_map:
            return
        update_expression = ', '.join([f'#{key} = :{key}' for key in kv_update_map.keys()])
        expression_attribute_names = {f'#{key}': key for key in kv_update_map.keys()}
        expression_attribute_values = {f':{key}': value for key, value in kv_update_map.items()}
        try:
            response = self.table.update_item(
                Key={
                    'parent': parent,
                    'child': child
                },
                UpdateExpression=f'set {update_expression}',
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                **kwargs
            )
            return response.get('Attributes', None)
        except ClientError as err:
            print("Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    def query(self, parent: str, child_namespace: str, **kwargs) -> List[ParentChildItem]:
        try:
            response = self.table.query(
                KeyConditionExpression=Key('parent').eq(parent) & Key('child').begins_with(child_namespace),
                ScanIndexForward=False,
                **kwargs)
        except ClientError as err:
            print("Couldn't query %s. Here's why: %s: %s", parent,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            response_items = response.get('Items', None) if response else None
            if not response:
                return []
            
            items = []
            for response_item in response_items:
                item: ParentChildItem = None
                parent = response_item.get('parent', None) if response_item else None
                child = response_item.get('child', None) if response_item else None
                if not (parent and child):
                    continue
                
                if parent.startswith(KeyNamespaces.LIBRARY.value) and child.startswith(KeyNamespaces.CONNECTION.value):
                    item = LibraryConnectionItem.from_dict(response_item)
                elif parent.startswith(KeyNamespaces.USER.value) and child.startswith(KeyNamespaces.LIBRARY.value):
                    item = UserLibraryItem.from_dict(response_item)
                if item:
                    items.append(item)
                else:
                    print("invalid item!")
                    print(response_item)
            return items
        
    def get(self, parent: str, child: str, **kwargs) -> ParentChildItem:
        try:
            response = self.table.get_item(
                Key={
                    'parent': parent,
                    'child': child,
                },
                **kwargs,
            )
        except ClientError as err:
            print("Couldn't query %s. Here's why: %s: %s", parent,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise
        else:
            response_item: Dict = response.get('Item', None) if response else []
            item: ParentChildItem = None
            parent = response_item.get('parent', None)
            child = response_item.get('child', None)
            if parent.startswith(KeyNamespaces.LIBRARY.value) and child.startswith(KeyNamespaces.CONNECTION.value):
                item = LibraryConnectionItem.from_dict(response_item)
            elif parent.startswith(KeyNamespaces.USER.value) and child.startswith(KeyNamespaces.LIBRARY.value):
                item = UserLibraryItem.from_dict(response_item)
            
            if not item:
                print("invalid item!")
            return item
        
    def delete(self, parent: str, child: str) -> None:
        try:
            self.table.delete_item(
                Key={
                    'parent': parent,
                    'child': child,
                },
            )
        except ClientError as err:
            print("Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise