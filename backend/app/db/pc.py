import json
from abc import ABC
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
class ParentChildItem(ABC):
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

@dataclass
class UserIntegrationItem(ParentChildItem):
    access_token: str
    refresh_token: str
    timestamp: int
    expiry_timestamp: int

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
                if item['child']:
                    if item['child'].startswith(KeyNamespaces.CHAT.value):
                        items.append(UserChatItem(**item))
                    if item['child'].startswith(KeyNamespaces.INTEGRATION.value):
                        items.append(UserIntegrationItem(**item))
                else:
                    print("invalid item!" + json.dumps(item))
            return items