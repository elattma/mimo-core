import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List


@dataclass
class Block(ABC):
    _LABEL = 'block'
    last_updated_timestamp: int

    def __str__(self) -> str:
        return json.dumps(self.get_as_dict())

    @abstractmethod
    def get_as_dict(self) -> dict:
        raise NotImplementedError('get_as_dict not implemented')

    @staticmethod
    def from_dict(label: str, block_dict: dict):
        last_updated_timestamp = block_dict.get('last_updated_timestamp')
        if label == SummaryBlock._LABEL:
            return SummaryBlock(
                last_updated_timestamp=last_updated_timestamp,
                text=block_dict.get('text')
            )
        elif label == BodyBlock._LABEL:
            return BodyBlock(
                last_updated_timestamp=last_updated_timestamp,
                text=block_dict.get('text')
            )
        elif label == MemberBlock._LABEL:
            name_dict: dict = block_dict.get('name')
            return MemberBlock(
                last_updated_timestamp=last_updated_timestamp,
                name=entity(
                    id=name_dict.get('id'),
                    value=name_dict.get('value')
                ),
                relation=Relations(block_dict.get('relation'))
            )
        elif label == TitleBlock._LABEL:
            return TitleBlock(
                last_updated_timestamp=last_updated_timestamp,
                text=block_dict.get('text')
            )
        elif label == CommentBlock._LABEL:
            author_dict: dict = block_dict.get('author')
            return CommentBlock(
                last_updated_timestamp=last_updated_timestamp,
                author=entity(
                    id=author_dict.get('id'),
                    value=author_dict.get('value')
                ),
            )
        elif label == DealBlock._LABEL:
            owner_dict: dict = block_dict.get('owner')
            name_dict: dict = block_dict.get('name')
            contact_dict: dict = block_dict.get('contact')
            return DealBlock(
                last_updated_timestamp=last_updated_timestamp,
                owner=entity(
                    id=owner_dict.get('id'),
                    value=owner_dict.get('value')
                ),
                name=entity(
                    id=name_dict.get('id'),
                    value=name_dict.get('value')
                ),
                contact=entity(
                    id=contact_dict.get('id'),
                    value=contact_dict.get('value')
                ),
                type=block_dict.get('type'),
                stage=block_dict.get('stage'),
                close_date=block_dict.get('close_date'),
                amount=block_dict.get('amount'),
                probability=block_dict.get('probability')
            )


class BlockStream:
    label: str
    blocks: List[Block]

    def __init__(self, label: str, blocks: List[Block]):
        self.label = label
        self.blocks = [block for block in blocks]

    def __str__(self) -> str:
        return json.dumps(self.get_as_dict())

    def get_as_dict(self) -> dict:
        return [block.get_as_dict() for block in self.blocks]

    @staticmethod
    def from_dict(label: str, block_dicts: List[dict]):
        blocks: List[Block] = []
        for block_dict in block_dicts:
            blocks.append(Block.from_dict(label, block_dict))

        return BlockStream(label, blocks)


@dataclass
class SummaryBlock(Block):
    _LABEL = 'summary'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }


@dataclass
class BodyBlock(Block):
    _LABEL = 'body'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }


class Relations(Enum):
    AUTHOR = 'author'
    RECIPIENT = 'recipient'
    PARTICIPANT = 'participant'


@dataclass
class entity:
    id: str
    value: str

    def __hash__(self) -> int:
        return hash(self.id)

    def get_as_dict(self) -> dict:
        return {
            'id': self.id,
            'value': self.value
        }


@dataclass
class MemberBlock(Block):
    _LABEL = 'member'
    name: entity
    relation: Relations

    def get_as_dict(self) -> dict:
        return {
            'name': self.name.get_as_dict(),
            'relation': self.relation.value if self.relation else None
        }


@dataclass
class TitleBlock(Block):
    _LABEL = 'title'
    text: str

    def get_as_dict(self) -> dict:
        return {
            'text': self.text
        }

# TODO: change to 1 block for all comments, but they have a chunkify method


@dataclass
class CommentBlock(Block):
    _LABEL = 'comment'
    author: entity
    text: str

    def get_as_dict(self) -> dict:
        return {
            'author': self.author.get_as_dict(),
            'text': self.text
        }


@dataclass
class DealBlock(Block):
    _LABEL = 'deal'
    owner: entity
    name: entity
    contact: entity
    type: str
    stage: str
    close_date: str
    amount: int
    probability: int

    def get_as_dict(self) -> dict:
        return {
            'owner': self.owner.get_as_dict(),
            'name': self.name.get_as_dict(),
            'contact': self.contact.get_as_dict(),
            'type': self.type,
            'stage': self.stage,
            'close_date': self.close_date,
            'amount': self.amount,
            'probability': self.probability
        }


@dataclass
class ContactBlock(Block):
    _LABEL = 'contact'
    name: entity
    created_by: entity
    department: str
    title: str
    lead_source: str

    def get_as_dict(self) -> dict:
        return {
            'name': self.name.get_as_dict(),
            'created_by': self.created_by.get_as_dict(),
            'department': self.department,
            'title': self.title,
            'lead_source': self.lead_source
        }
