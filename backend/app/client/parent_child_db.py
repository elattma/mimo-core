import json
from dataclasses import dataclass
from enum import Enum
from typing import List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


class KeyNamespaces(Enum):
    USER = "USER#"
    CHAT = "CHAT#"
    INTEGRATION = "INTEGRATION#"

class Roles(Enum):
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ParentChildItem:
    parent: str
    child: str

    def get_raw_parent(self):
        if not self.parent:
            return None
        return self.parent.split('#')[-1]
    
    def get_raw_child(self):
        if not self.child:
            return None
        return self.child.split('#')[-1]
    

@dataclass
class UserChatItem(ParentChildItem):
    message: str
    author: str
    role: str
    timestamp: int

    @staticmethod
    def from_dict(item: dict):
        if not item:
            return None

        parent = item.get('parent', None)
        child = item.get('child', None)
        message = item.get('message', None)
        author = item.get('author', None)
        role = item.get('role', None)
        timestamp = item.get('timestamp', None)

        if not (parent and child and message and author and role and timestamp):
            return None
        
        return UserChatItem(
            parent=parent,
            child=child,
            message=message,
            author=author,
            role=role,
            timestamp=int(timestamp),
        )

@dataclass
class UserIntegrationItem(ParentChildItem):
    access_token: str = None
    refresh_token: str = None
    timestamp: int = None
    expiry_timestamp: int = None
    last_fetch_timestamp: int = None

    @staticmethod
    def from_dict(item: dict):
        if not item:
            return None

        parent = item.get('parent', None)
        child = item.get('child', None)

        if not (parent and child):
            return None
        
        return UserIntegrationItem(
            parent=parent,
            child=child,
            access_token=item.get('access_token', None),
            refresh_token=item.get('refresh_token', None),
            timestamp=item.get('timestamp', None),
            expiry_timestamp=item.get('expiry_timestamp', None),
            last_fetch_timestamp=item.get('last_fetch_timestamp', None),
        )

class ParentChildDB:
    table = None
    def __init__(self, table_name: str):
        if not self.table:
            self.table = boto3.resource('dynamodb').Table(table_name)
            self.table.load()
        
    def write(self, items: List[ParentChildItem]):
        try:
            with self.table.batch_writer() as writer:
                for item in items:
                    writer.put_item(Item=item.__dict__)
        except ClientError as err:
            print("Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                err.response['Error']['Code'], err.response['Error']['Message'])
            raise

    # TODO: generalize
    def update(self, items: List[ParentChildItem], **kwargs):
        if not kwargs or len(kwargs) < 1:
            return
        update_expression = ', '.join([f'#{key} = :{key}' for key in kwargs.keys()])
        expression_attribute_names = {f'#{key}': key for key in kwargs.keys()}
        expression_attribute_values = {f':{key}': value for key, value in kwargs.items()}
        for item in items:
            try:
                self.table.update_item(
                    Key={
                        'parent': item.parent,
                        'child': item.child
                    },
                    UpdateExpression=f'set {update_expression}',
                    ExpressionAttributeNames=expression_attribute_names,
                    ExpressionAttributeValues=expression_attribute_values,
                )
            except ClientError as err:
                print("Couldn't load data into table %s. Here's why: %s: %s", self.table.name,
                    err.response['Error']['Code'], err.response['Error']['Message'])
                raise

    def query(self, parent: str, child_namespace: str, **kwargs):
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
                parent = response_item.get('parent', None) if response_item else None
                child = response_item.get('child', None) if response_item else None
                if not child:
                    continue
                
                item: ParentChildItem = None
                if child.startswith(KeyNamespaces.CHAT.value):
                    item = UserChatItem.from_dict(response_item)
                elif child.startswith(KeyNamespaces.INTEGRATION.value):
                    item = UserIntegrationItem.from_dict(response_item)
                
                if not item:
                    print("invalid item!")
                    print(response_item)
                    continue

                items.append(item)
            return items