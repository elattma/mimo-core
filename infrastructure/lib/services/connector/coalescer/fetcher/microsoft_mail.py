from typing import Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher
from fetcher.model import StreamData


class MicrosoftMail(Fetcher):
    _INTEGRATION = 'microsoft_mail'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def discover(self) -> Generator[StreamData, None, None]:
        return []

    def fetch(self, stream: StreamData) -> None:
        return
