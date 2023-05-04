from typing import Dict, Generator, List

import boto3
from shared.model import Integration


class SSM:
    _ssm = None

    def __init__(self) -> None:
        if not self._ssm:
            self._ssm = boto3.client('ssm')

    def _get_by_path(self, path: str) -> Generator[Dict, None, None]:
        next_token = None
        while True:
            response: Dict = self._ssm.get_parameters_by_path(
                Path=path,
                Recursive=True,
                WithDecryption=True,
                **({'NextToken': next_token} if next_token is not None else {})
            )
            next_token = response.get('NextToken', None)
            for parameter in response.get('Parameters', []):
                yield parameter
            if next_token is None:
                break
    
    def load_params(self, path: str) -> Dict[str, Dict | str]:
        params: Dict[str, Dict | str] = {}
        base_len = len(path.split('/'))
        param_generator = self._get_by_path(path)
        for parameter in param_generator:
            path_list = parameter.get('Name', '').split('/')
            if len(path_list) < base_len:
                continue
            path_list = path_list[base_len:]
            accumulator = params
            for name in path_list[:-1]:
                if not accumulator.get(name, None):
                    accumulator[name] = {}
                accumulator = accumulator[name]
            accumulator[path_list[-1]] = parameter.get('Value')
        return params
