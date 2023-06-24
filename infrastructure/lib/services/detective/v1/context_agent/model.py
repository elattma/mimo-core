from dataclasses import dataclass
from typing import List, Optional

from dstruct.model import BlockQuery, RelativeTime, SearchMethod
from pydantic import BaseModel


@dataclass
class Request:
    raw: str
    token_limit: int = None
    next_token: str = None
    start: BlockQuery = None
    end: BlockQuery = None

class ContextQuery(BaseModel):
    lingua: Optional[str]
    integrations: Optional[List[str]]
    concepts: Optional[List[str]]
    entities: Optional[List[str]]
    time_start: Optional[int]
    time_end: Optional[int]
    time_sort: Optional[RelativeTime]
    limit: Optional[int]
    offset: Optional[int]
    search_method: Optional[SearchMethod]
    