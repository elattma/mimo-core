import json
from typing import Any, Dict, Generator, List

import requests
from auth.base import AuthType
from fetcher.base import Fetcher, StreamData


class Linear(Fetcher):
    _INTEGRATION = 'linear'
    
    def _get_supported_auth_types(self) -> List[AuthType]:
        return [AuthType.TOKEN_OAUTH2, AuthType.TOKEN_DIRECT, AuthType.BASIC]
    
    def _discover_helper(self, model: str, label: str) -> Generator[StreamData, None, None]:
        next_token = 0
        limit = self._filter.limit if self._filter else None
        while True:
            pagination = 'first: 100' + (f', after: "{next_token}"' if next_token else '')
            query = (
                'query {'
                f'  {model}({pagination}) '
                '{    nodes {'
                '      id'
                '    }'
                '  }'
                '}'
            )
            response = self.request('https://api.linear.app/graphql', method='post', json={
                'query': query
            })
            nodes = response.get('data', {}).get(model, {}).get('nodes', [])
            if not nodes:
                break

            for node in nodes:
                id = node.get('id', None)
                if not id:
                    continue
                yield StreamData(name=label, id=id)
                if limit:
                    limit -= 1
                    if limit < 1:
                        return []
            if len(nodes) < 100:
                break
            next_token += 100

    def discover(self) -> Generator[StreamData, None, None]:
        yield from self._discover_helper('issues', 'ticket')
        yield from self._discover_helper('users', 'user')
        yield from self._discover_helper('comments', 'comment')
        yield from self._discover_helper('projects', 'project')

    def fetch(self, stream: StreamData) -> None:
        model = stream._name
        if stream._name == 'ticket':
            model = 'issue'
            fields = [
                'id',
                'assignee',
                'completedAt',
                'createdAt',
                'creator',
                'description',
                'dueDate',
                'estimate',
                'parent',
                'priority',
                'project',
                'updatedAt',
            ]
        elif stream._name == 'user':
            fields = [
                'id',
                'active',
                'admin',
                'description',
                'email',
                'name',
                'updatedAt',
            ]
        elif stream._name == 'comment':
            fields = [
                'id',
                'body',
                'createdAt',
                'creator',
                'issue',
                'updatedAt',
            ]
        elif stream._name == 'project':
            fields = [
                'id',
                'completedAt',
                'creator',
                'progress',
                'scope',
                'state',
                'description',
                'name',
                'updatedAt',
            ]
        else:
            raise ValueError(f'Unsupported stream: {stream._name}')
        
        query = f"""
        {{
            {model}(id: "{stream._id}") {{
                {' '.join(fields)}
            }}
        }}
        """

        response = self.request('https://api.linear.app/graphql', method='post', json={
            'query': query
        })
        data = response.get('data', {}).get(model, {}) if response else {}
        for key, value in data.items():
            stream.add_structured_data(key, str(value) if value else None)
