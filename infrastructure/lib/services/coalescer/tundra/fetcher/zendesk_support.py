from typing import Generator, List

from .base import Discovery, Fetcher, Section


class ZendeskSupport(Fetcher):
    _INTEGRATION = 'zendesk_support'

    def discover(self) -> Generator[Discovery, None, None]:
        print('zendesk support discovery!')

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('zendesk support fetch!')
