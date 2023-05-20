from typing import Generator, List

from base import Discovery, Fetcher, Section


class MicrosoftMail(Fetcher):
    _INTEGRATION = 'microsoft_mail'

    def discover(self) -> Generator[Discovery, None, None]:
        print('microsoft mail discovery!')

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('microsoft mail fetch!')

