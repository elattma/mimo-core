from typing import Any, Dict, Generator, List

from auth.base import AuthType
from fetcher.base import Fetcher, StreamData


class Clickup(Fetcher):
    _INTEGRATION = 'clickup'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def _discover_helper(self, endpoint: str, label: str, response_key: str, paginated: bool = False, params: Dict[str, Any] = {}) -> Generator[StreamData, None, None]:
        next_token = 0
        limit = self._filter.limit if self._filter else None
        while True:
            params.update({
                'page': next_token,
            })
            response = self.request(endpoint, params=params)
            data_list: List[Dict] = response.get(response_key, []) if response else []
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
            next_token += 1
            if not paginated:
                break

    def discover(self) -> Generator[StreamData, None, None]:
        teams = self._discover_helper('https://api.clickup.com/api/v2/team', 'team', 'teams')
        for team in teams:
            yield team
            yield from self._discover_helper(f'https://api.clickup.com/api/v2/team/{team._id}/task', 'ticket', 'tasks', True, {
                'subtasks': True,
                'include_closed': True,
            })
            yield from self._discover_helper(f'https://api.clickup.com/api/v2/team/{team._id}/comment', 'comment', 'comments')
            yield from self._discover_helper(f'https://api.clickup.com/api/v2/team/{team._id}/goal', 'goal', 'goals', False, {
                'include_completed': True,
            })

    def _fetch_helper(self, endpoint: str, stream: StreamData) -> None:
        response = self.request(endpoint)
        data: Dict[str, Any] = response.get('data', None) if response else None
        if not data:
            return

        for key, value in data.items():
            stream.add_structured_data(key, str(value) if value else None)

    def fetch(self, stream: StreamData) -> None:
        if stream._name == 'team':
            self._fetch_helper(f'https://api.clickup.com/api/v2/team/{stream._id}', stream)
        elif stream._name == 'ticket':
            self._fetch_helper(f'https://api.clickup.com/api/v2/task/{stream._id}', stream)
        elif stream._name == 'comment':
            self._fetch_helper(f'https://api.clickup.com/api/v2/comment/{stream._id}', stream)
        elif stream._name == 'goal':
            self._fetch_helper(f'https://api.clickup.com/api/v2/goal/{stream._id}', stream)
        else:
            raise ValueError(f'Unsupported stream: {stream._name}')