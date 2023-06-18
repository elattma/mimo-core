from typing import Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher
from fetcher.model import StreamData


class WebLink(Fetcher):
    _INTEGRATION = 'web_link'
    
    def _get_supported_auth_types(sef) -> List[AuthType]:
        return []

    def discover(self) -> Generator[StreamData, None, None]:
        links = self._config.get('links', None) if self._config else None
        for link in links:
            yield StreamData(
                name='website',
                id=link,
            )

    def fetch_website(self, stream: StreamData) -> None:
        from unstructured.partition.html import partition_html

        link = stream._id if stream else None
        if not link:
            raise Exception(f'WebLink.fetch() invalid config.. {self._config}')
        
        elements = partition_html(url=link)
        if not elements:
            raise Exception(f'WebLink.fetch() no elements found.. {link}')

        for element in elements:
            stream.add_unstructured_data('element', str(element))
        
        stream._id = stream._id.replace('http://', '').replace('https://', '').replace('/', '_')

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'website':
            self.fetch_website(stream)

