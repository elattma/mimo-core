from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from mystery.query import Query, Request


@dataclass
class Block:
    id: str
    label: str
    last_updated_timestamp: int
    blocks: List[Dict]
    embedding: List[float] = None

@dataclass
class Context:
    connection: str
    source: str
    blocks: List[Block]
    tokens: int = None

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
        stringified += '\n'.join([str(context.blocks) for context in self.contexts])
        return stringified

@dataclass
class DataError(Enum):
    QUERY_FORMATION_FAILURE = 'Failed to dynamically formulate query!'
    FETCH_PAGES_FAILURE = 'Failed to fetch pages!'
    FILTERED_PAGES_FAILURE = 'Failed to fetched filtered pages!'
    DECORATE_EMBEDDINGS_FAILURE = 'Failed to decorate pages with embeddings!'
    WEAVE_CONTEXT_FAILURE = 'Failed to weave context!'
    MINIFY_CONTEXT_FAILURE = 'Failed to minify context!'

@dataclass
class DataRequest:
    library: str
    request: str
    query: Query
    max_tokens: int

@dataclass
class DataResponse:
    successful: bool
    context_basket: ContextBasket
    error: DataError = None