from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, List

from app.auth.base import Auth

MAX_TEXT_SIZE = 600
MAX_TEXT_OVERLAP = 50

@dataclass
class Filter:
    next_token: str = None
    limit: int = 20


@dataclass
class Item:
    id: str
    title: str
    link: str
    preview: str


@dataclass
class DiscoveryResponse:
    integration: str
    icon: str
    items: List[Item]
    next_token: str


@dataclass
class Block(ABC):
    pass

@dataclass
class SummaryBlock(Block):
    summary: str

@dataclass
class BodyBlock(Block):
    body: str

@dataclass
class TitleBlock(Block):
    title: str

# TODO: change to 1 block for all comments, but they have a chunkify method
# class Comment:
#     author: str
#     text: str

@dataclass
class CommentsBlock(Block):
    comments: str

class Fetcher(ABC):
    _INTEGRATION = "base"

    subclasses = {}

    # TODO: add last sync time to filter only updated documents

    @classmethod
    def create(cls, integration, auth_params: dict, **kwargs):
        if not cls.subclasses:
            cls.subclasses = {
                subclass._INTEGRATION: subclass for subclass in cls.__subclasses__()
            }

        if not integration or not cls.subclasses.get(integration, None):
            print(f"integration auth not found for {integration}")
            return None

        fetcher = cls.subclasses[integration]()
        fetcher_auth_overrides = fetcher.get_auth_attributes()
        if fetcher_auth_overrides:
            auth_params.update(fetcher_auth_overrides)
        fetcher.define_auth(fetcher.get_auth_type(), **auth_params)
        fetcher.init(**kwargs)

        return fetcher

    def init(self, last_fetch_timestamp: int = None):
        self.last_fetch_timestamp = last_fetch_timestamp

    def define_auth(self, auth_type: str, **kwargs):
        self.auth = Auth.create(auth_type, **kwargs)
        self.auth.validate()

    def get_icon(self) -> str:
        return f"assets.mimo.team/icons/{self._INTEGRATION}.svg"

    @abstractmethod
    def get_auth_type(self) -> str:
        raise NotImplementedError("get_auth_type not implemented")

    @abstractmethod
    def get_auth_attributes(self) -> dict:
        raise NotImplementedError("get_auth_attributes not implemented")

    @abstractmethod
    def discover(self, filter: Filter = None) -> DiscoveryResponse:
        raise NotImplementedError("discover not implemented")

    @abstractmethod
    def fetch(self, id: str) -> Generator[Block, None, None]:
        raise NotImplementedError("fetch not implemented")

    def _merge_texts(self, texts: List[str]) -> str:
        return "\n\n".join([text for text in texts])

    def _merge_split_texts(self, texts: List[str]) -> List[str]:
        if not texts or len(texts) < 1:
            return []
        final_texts: List[str] = []
        temporary_texts: List[str] = []
        total_texts_size = 0
        for text in texts:
            if not text:
                continue
            text_size = len(text)
            if text_size < 1:
                continue

            if total_texts_size + text_size >= MAX_TEXT_SIZE:
                if total_texts_size > MAX_TEXT_SIZE:
                    print(f"Created a text of size {total_texts_size}")

                if len(temporary_texts) > 0:
                    final_texts.append(self._merge_texts(temporary_texts))
                    while total_texts_size > MAX_TEXT_OVERLAP or (
                        total_texts_size + text_size > MAX_TEXT_SIZE
                        and total_texts_size > 0
                    ):
                        total_texts_size -= len(temporary_texts[0])
                        temporary_texts.pop(0)

            temporary_texts.append(text)
            total_texts_size += text_size

        if len(temporary_texts) > 0:
            final_texts.append(self._merge_texts(temporary_texts))

        return final_texts
