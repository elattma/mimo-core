from typing import Dict, Generator

import boto3


class SSM:
    _ssm = None

    def __init__(self) -> None:
        if not self._ssm:
            self._ssm = boto3.client('ssm')

    def _get_by_path(self, path: str) -> Generator[Dict, None, None]:
        next_token = None
        while True:
            response = self._ssm.get_parameters_by_path(
                Path=path,
                Recursive=True,
                **({'NextToken': next_token} if next_token is not None else {})
            )
            next_token = response.get('NextToken')
            for parameter in response['Parameters']:
                yield parameter
            if next_token is None:
                break
    
    def load_nested_params(self, path: str) -> Dict[str, dict]:
        params: Dict[str, dict] = {}
        param_generator = self._get_by_path(path)
        for parameter in param_generator:
            path_list = parameter.get('Name', '').split('/')
            if len(path_list) < 3:
                print('failed to parse parameter path!')
                continue
            id = path_list[-2]
            key = path_list[-1]
            value = parameter.get('Value')
            if id and key and value:
                if not params.get(id, None):
                    params[id] = {
                        f'{key}': value
                    }
                else:
                    params[id].update({
                        f'{key}': value
                    })
        return params
    
    def load_params(self, path: str) -> Dict:
        params: Dict = {}
        param_generator = self._get_by_path(path)
        for parameter in param_generator:
            path_list = parameter.get('Name', '').split('/')
            if len(path_list) < 2:
                print('failed to parse parameter path!')
                continue
            key = path_list[-1]
            value = parameter.get('Value')
            if key and value:
                params[key] = value
        return params