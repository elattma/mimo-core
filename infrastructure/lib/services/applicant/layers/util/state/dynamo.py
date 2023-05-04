from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from shared.model import App


class KeyNamespaces(Enum):
    USER = "USER#"
    LIBRARY = "LIBRARY#"
    APP = "APP#"

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
class ParentAppItem(ParentChildItem):
    app: App = None

    def get_raw_child(self):
        return self.app.id if self.app else None

    def get_child(self):
        return KeyNamespaces.APP.value + self.app.id if self.app else None

    def is_valid(self):
        return self.parent and self.app and self.app.is_valid()

    def as_dict(self):
        if not self.is_valid():
            return None
        
        return {
            'parent': self.parent,
            'child': self.get_child(),
            'name': self.app.name,
            'created_at': self.app.created_at
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
        app = App(
            id=child.split('#')[-1],
            name=name,
            created_at=int(created_at) if created_at else None,
        )

        return ParentAppItem(
            parent=parent,
            app=app,
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
                
                if child.startswith(KeyNamespaces.APP.value):
                    item = ParentAppItem.from_dict(response_item)
                if item:
                    items.append(item)
                else:
                    print("invalid item!")
                    print(response_item)
            return items
        
    def get(self, parent: str, child: str) -> ParentChildItem:
        try:
            response = self.table.get_item(
                Key={
                    'parent': parent,
                    'child': child,
                }
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
            if child.startswith(KeyNamespaces.APP.value):
                item = ParentAppItem.from_dict(response_item)
            
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