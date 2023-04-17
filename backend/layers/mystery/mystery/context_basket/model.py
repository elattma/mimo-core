from dataclasses import dataclass, field
from enum import Enum
from typing import List

from graph.neo4j_ import Block
from mystery.query import Query, Request


@dataclass
class Source:
    page_id: str
    integration: str

@dataclass
class Context:
    source: Source
    blocks: List[Block]
    translated: str
    tokens: int

@dataclass
class ContextBasket:
    request: Request
    contexts: List[Context] = field(default_factory=list)
    tokens: int = 0

    def append(self, context: Context) -> None:
        self.tokens += context.tokens
        self.contexts.append(context)

    def extend(self, contexts: List[Context]) -> None:
        for context in contexts:
            self.tokens += context.tokens
        self.contexts.extend(contexts)

    def pop(self, pos: int = -1) -> Context:
        if self.contexts:
            context = self.contexts.pop(pos)
            self.tokens -= context.tokens
            return context

    def __iter__(self):
        return iter(self.contexts)

    def __str__(self):
        stringified = self.request.text
        stringified += '\n--------\n'
        stringified += '\n'.join([context.translated for context in self.contexts])
        return stringified

@dataclass
class DataError(Enum):
    QUERY_FORMATION_FAILURE = 'Failed to dynamically formulate query!'
    FETCH_DOCUMENTS_FAILURE = 'Failed to fetch documents!'
    FILTERED_DOCUMENTS_FAILURE = 'Failed to fetched filtered documents!'
    DECORATE_EMBEDDINGS_FAILURE = 'Failed to decorate documents with embeddings!'
    WEAVE_CONTEXT_FAILURE = 'Failed to weave context!'
    MINIFY_CONTEXT_FAILURE = 'Failed to minify context!'

@dataclass
class DataRequest:
    request: str
    query: Query = None
    page_ids: List[str] = None
    max_tokens: int = None

@dataclass
class DataResponse:
    successful: bool
    context_basket: ContextBasket
    error: DataError = None