from dataclasses import dataclass, field
from typing import List

from graph.neo4j_ import Block


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
class Request:
    encoding_name: str
    text: str
    embedding: List[float]

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

    def __iter__(self):
        return iter(self.contexts)

    def __str__(self):
        stringified = self.request.text
        stringified += '\n--------\n'
        stringified += '\n'.join([context.translated for context in self.contexts])
        return stringified
