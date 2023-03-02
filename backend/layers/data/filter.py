from dataclasses import dataclass


@dataclass
def FetcherFilter():
    next_token: str = None
    limit: int = 20
    