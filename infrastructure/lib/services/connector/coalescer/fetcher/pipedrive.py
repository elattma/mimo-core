from typing import Any, Dict, Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher, StreamData


class Pipedrive(Fetcher):
    _INTEGRATION = 'pipedrive'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def _discover_helper(self, endpoint: str, label: str) -> Generator[StreamData, None, None]:
        next_token = 0
        params = {}
        limit = self._filter.limit if self._filter else None
        while True:
            params.update({
                'start': next_token,
                'limit': 100
            })
            response = self.request(endpoint, params=params)
            data_list: List[Dict] = response.get('data', []) if response else []
            if not data_list:
                break
            for data in data_list:
                id = data.get('id', None)
                if not id:
                    continue
                yield StreamData(name=label, id=id)
                if limit:
                    limit -= 1
                    if limit < 1:
                        return []
            if len(data) < 100:
                break

    def discover(self) -> Generator[StreamData, None, None]:
        yield from self._discover_helper('https://api.pipedrive.com/v1/deals', 'deal')
        yield from self._discover_helper('https://api.pipedrive.com/v1/organizations', 'organization')
        yield from self._discover_helper('https://api.pipedrive.com/v1/activities', 'activity')
        yield from self._discover_helper('https://api.pipedrive.com/v1/leads', 'lead')
        yield from self._discover_helper('https://api.pipedrive.com/v1/notes', 'note')
        yield from self._discover_helper('https://api.pipedrive.com/v1/files', 'document')
        yield from self._discover_helper('https://api.pipedrive.com/v1/users', 'user')
    
    def _fetch_helper(self, endpoint: str, stream: StreamData) -> None:
        response = self.request(endpoint)
        data: Dict[str, Any] = response.get('data', None) if response else None
        if not data:
            return

        for key, value in data.items():
            stream.add_structured_data(key, str(value) if value else None)

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'deal':
            self._fetch_helper(f'https://api.pipedrive.com/v1/deals/{stream._id}', stream)
        elif stream._name == 'organization':
            self._fetch_helper(f'https://api.pipedrive.com/v1/organizations/{stream._id}', stream)
        elif stream._name == 'activity':
            self._fetch_helper(f'https://api.pipedrive.com/v1/activities/{stream._id}', stream)
        elif stream._name == 'lead':
            self._fetch_helper(f'https://api.pipedrive.com/v1/leads/{stream._id}', stream)
        elif stream._name == 'note':
            self._fetch_helper(f'https://api.pipedrive.com/v1/notes/{stream._id}', stream)
        elif stream._name == 'document':
            self._fetch_helper(f'https://api.pipedrive.com/v1/files/{stream._id}', stream)
        elif stream._name == 'user':
            self._fetch_helper(f'https://api.pipedrive.com/v1/users/{stream._id}', stream)
        else:
            raise ValueError(f'Unsupported stream: {stream._name}')