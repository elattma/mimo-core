from typing import Any, Dict, Generator, List

import boto3


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
    
    def load_params(self, path: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
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

    def set_param(self, path: str, value: str) -> bool:
        response = self._ssm.put_parameter(
            Name='{path}'.format(path=path),
            Value=value,
            Type='SecureString',
            Overwrite=True
        )
        return response.get('ResponseMetadata', {}).get('HTTPStatusCode', 0) == 200