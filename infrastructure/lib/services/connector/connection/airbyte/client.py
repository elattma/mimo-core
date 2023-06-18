from typing import Dict

import requests
from airbyte.source_configs import source_definition_id_to_config
from auth.base import AuthStrategy


class Airbyte:
    def __init__(self, endpoint: str):
        self._endpoint = endpoint
        workspaces = self._call('workspaces/list')
        workspace_id = workspaces.get('workspaces', [{}])[0].get('workspaceId', None) if workspaces else None
        print('[init] workspace_id:', workspace_id)
        self._workspace_id = workspace_id

        if not self._workspace_id:
            raise Exception('[init] failed')

    def _call(self, route: str, json: Dict = None) -> Dict:
        url = f'{self._endpoint}/v1/{route}'
        print('[call_airbyte] url:', url, ', with json:', json if json and route != 'web_backend/connections/update' else 'None')
        response = requests.post(url, json=json)
        print('[call_airbyte] response status:', response.status_code if response else 'None')
        if not response:
            return None
        try:
            response = response.json()
        except Exception as e:
            print('[call_airbyte] error:', str(e))
            response = response.status_code
        return response

    def _check_connection(self, source_id: str, delete_if_invalid: bool = True) -> bool:
        check = self._call('sources/check_connection', { 'sourceId': source_id })
        if check == 200 or check.get('status', None) == 'succeeded':
            print(f'[check_connection] source {source_id} succeeded')
            return True
        
        print(f'[check_connection] source {source_id} failed')
        return False

    def _with_catalog(self, library: str, connection_id: str) -> bool:
        with_catalog = self._call('web_backend/connections/get', {
            'connectionId': connection_id,
            'withRefreshedCatalog': True
        })
        if not with_catalog:
            print('[with_catalog] with_catalog failed')
            return False

        with_catalog['namespaceFormat'] = f'{library}/{connection_id}'
        streams = with_catalog.get('syncCatalog', {}).get('streams', [])
        for stream in streams:
            stream.get('config', {})['selected'] = True
            stream.get('config', {})['destinationSyncMode'] = 'overwrite'

        update_catalog = self._call('web_backend/connections/update', with_catalog)
        if not update_catalog:
            print('[with_catalog] update_catalog failed')
            return False
        print('[with_catalog] update_catalog succeeded')
        return True

    def _create_connection(self, library: str, source_id: str, destination_id: str) -> str:
        connection = self._call('connections/create', {
            'workspaceId': self._workspace_id,
            'sourceId': source_id,
            'destinationId': destination_id,
            'name': library,
            'namespaceDefinition': 'customformat',
            'namespaceFormat': f'{library}/{source_id}',
            'scheduleType': 'manual',
            'status': 'active'
        })
        connection_id = connection.get('connectionId', None) if connection else None
        print('[create_connection] connection_id:', connection_id)
        return connection_id

    def _create_source(self, source_definition_id: str, strategy: AuthStrategy, name: str) -> str:
        config_function = source_definition_id_to_config.get(source_definition_id, None)
        config = config_function(strategy) if config_function else None
        print('[create_source] config:', config)
        if not config:
            print('[create_source] error generating config!')
            return None
        
        source = self._call('sources/create', { 'sourceDefinitionId': source_definition_id, 'workspaceId': self._workspace_id, 'connectionConfiguration': config, 'name': name })
        source_id = source.get('sourceId', None) if source else None
        print('[create_source] source_id:', source_id)
        return source_id
    
    def _delete_source(self, source_id: str) -> bool:
        deleted = self._call('sources/delete', { 'sourceId': source_id })
        print('[delete_source] source_id:', source_id, 'deleted:', deleted)
        return deleted == 204

    def create(self,
               strategy: AuthStrategy,
               library: str,
               name: str,
               source_definition_id: str) -> str:
        source_id = self._create_source(source_definition_id, strategy, name)
        if not (source_id and self._check_connection(source_id)):
            return None
        
        connection_id = self._create_connection(library, source_id, 'f23e7454-0fac-44f9-aa68-b4d7c3feb75a')
        if not connection_id:
            self._delete_source(source_id)
            return None
        
        added_catalog = self._with_catalog(library, connection_id)
        if not added_catalog:
            self._delete_source(source_id)
            return None
        
        return connection_id
    
    def delete(self, connection_id: str) -> bool:
        connection = self._call('connections/get', { 'connectionId': connection_id })
        if not connection:
            print('[delete] connection not found')
            return False
        
        source_id = connection.get('sourceId', None) if connection else None
        if not source_id:
            print('[delete] source id not found')
            return False

        deleted = self._call('sources/delete', { 'sourceId': source_id })
        print('[delete] connection_id:', connection_id, 'source_id:', source_id, 'deleted:', deleted)
        if deleted != 204:
            return False
        return True
    