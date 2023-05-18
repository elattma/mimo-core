from typing import Generator, List

from base import Discovery, Fetcher, Section


class IntercomSupport(Fetcher):
    _INTEGRATION = 'intercom_support'

    def get_auth_type(self) -> str:
        return 'oauth'
    
    def get_auth_attributes(self) -> dict:
        return {
        }

    def discover(self) -> Generator[Discovery, None, None]:
        print('intercom discovery!')


    def fetch(self, discovery: Discovery) -> List[Section]:
        print('intercom fetch!')
