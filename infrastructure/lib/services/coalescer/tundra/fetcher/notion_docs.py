from typing import Generator, List

from .base import Discovery, Fetcher, Section


class NotionDocs(Fetcher):
    _INTEGRATION = 'notion_docs'

    def discover(self) -> Generator[Discovery, None, None]:
        print('notion docs discovery!')

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('notion docs fetch!')

