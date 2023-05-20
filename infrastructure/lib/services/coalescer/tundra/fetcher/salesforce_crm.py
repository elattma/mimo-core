from typing import Generator, List

from base import Discovery, Fetcher, Section


class SalesforceCrm(Fetcher):
    _INTEGRATION = 'salesforce_crm'

    def discover(self) -> Generator[Discovery, None, None]:
        print('salesforce crm discovery!')

    def fetch(self, discovery: Discovery) -> List[Section]:
        print('salesforce crm fetch!')
