from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError


class KeyNamespaces(Enum):
    USER = "USER#"
    MESSAGE = "MESSAGE#"

class ParentChildItem(ABC):
    def __init__(self, parent: str, child: str, parent_namespace: str, child_namespace: str):
        self.parent = parent_namespace + parent
        self.child = child_namespace + child

    @abstractmethod
    def to_dict(self):
        return {
            'parent': self.parent,
            'child': self.child
        }

    @staticmethod
    @abstractmethod
    def from_dict(d):
        pass

class UserMessageItem(ParentChildItem):
    def __init__(self, parent: str, child: str, author: str, message: str, timestamp: int):
        super().__init__(parent, child, KeyNamespaces.USER.value, KeyNamespaces.MESSAGE.value)
        self.author = author
        self.message = message
        self.timestamp = timestamp

    def to_dict(self):
        d = super().to_dict()
        d['author'] = str(self.author)
        d['message'] = str(self.message)
        d['timestamp'] = int(self.timestamp)
        return d

    def get_author(self):
        return self.author
    
    def get_message(self):
        return self.message

    @staticmethod
    def from_dict(d: Dict):
        return UserMessageItem(d['parent'], d['child'], d['author'], d['message'], d['timestamp'])


class ParentChildDB:
    def __init__(self, table_name: str):
        try: 
            table = boto3.resource('dynamodb').Table(table_name)
            table.load()
        except ClientError as err:
            print("Couldn't check for existence of %s. Here's why: %s: %s",
                table_name,
                err.response['Error']['Code'], err.response['Error']['Message']) # TODO: switch to powertools logging
            raise
        else:
            self.table = table
        
    def write(self, items: List[ParentChildItem]):
        try:
            with self.table.batch_writer() as writer:
                for item in items:
                    writer.put_item(Item=item.to_dict())
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
            if not response['Items']:
                return []
            items = []
            for item in response['Items']:
                if parent.startswith(KeyNamespaces.USER.value):
                    items.append(UserMessageItem.from_dict(item))
            return items