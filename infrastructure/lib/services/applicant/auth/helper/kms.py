import base64
import json
from time import time

import boto3

from .payload import Payload


class KMS:
    _client = None

    def __init__(self, region_name = 'us-east-1'):
        if not self._client:
            self._client = boto3.client('kms', region_name=region_name)

    def encrypt(self, payload: Payload, key_id: str) -> str:
        response = self._client.encrypt(
            KeyId=key_id,
            Plaintext=json.dumps(payload.to_dict()).encode()
        )
        encrypted = response.get('CiphertextBlob', None) if response else None
        if not encrypted:
            return None
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted: str, key_id: str) -> Payload:
        response = self._client.decrypt(
            KeyId=key_id,
            CiphertextBlob=base64.b64decode(encrypted)
        )
        decrypted = response.get('Plaintext', None) if response else None
        if not decrypted:
            return None
        decoded = decrypted.decode()
        return Payload(**json.loads(decoded))
