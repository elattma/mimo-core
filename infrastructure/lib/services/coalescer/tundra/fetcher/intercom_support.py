from typing import Generator, List

from .base import Discovery, Fetcher, Section


class IntercomSupport(Fetcher):
    _INTEGRATION = 'intercom_support'

    def discover(self) -> Generator[Discovery, None, None]:
        print('intercom discovery!')

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('intercom fetch!')
