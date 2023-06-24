from dataclasses import dataclass

from dstruct.model import BlockQuery


@dataclass
class Request:
    raw: str
    token_limit: int = None
    next_token: str = None
    start_block: BlockQuery = None
    end_block: BlockQuery = None
