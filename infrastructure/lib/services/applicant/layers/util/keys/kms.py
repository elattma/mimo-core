import base64
import json

import boto3

from .payload import Payload


class KMS:
    _client = None
    _HEADER = base64.b64encode(json.dumps({
        'alg': 'RS256',
        'typ': 'JWT'
    }).encode()).decode()

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
    
    def decrypt(self, token: str, key_id: str) -> Payload:
        response = self._client.decrypt(
            KeyId=key_id,
            CiphertextBlob=base64.b64decode(token)
        )
        decrypted = response.get('Plaintext', None) if response else None
        if not decrypted:
            return None
        decoded = decrypted.decode()
        return Payload(**json.loads(decoded))

    def sign(self, payload: Payload, key_id: str) -> str:
        token_components = {
            'header': self._HEADER,
            'payload': base64.b64encode(json.dumps(payload.to_dict()).encode()).decode()
        }
        message = '.'.join([token_components['header'], token_components['payload']])
        response = self._client.sign(
            KeyId=key_id,
            Message=message.encode(),
            MessageType='RAW',
            SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256'
        )
        
        signature = response.get('Signature', None) if response else None
        if not signature:
            return None
        
        token_components['signature'] = base64.b64encode(signature).decode() \
                                              .replace('+', '-') \
                                              .replace('/', '_') \
                                              .replace('=', '')
        return '.'.join([token_components['header'], token_components['payload'], token_components['signature']])
    
    def verify(self, token: str, key_id: str) -> Payload:
        token_components = token.split('.')
        if len(token_components) != 3:
            return None
        header = token_components[0]
        payload = token_components[1]
        signature = token_components[2]
        message = '.'.join([header, payload])

        signature = signature.replace('-', '+') \
                                .replace('_', '/') + '=='
        response = self._client.verify(
            KeyId=key_id,
            Message=message.encode(),
            MessageType='RAW',
            Signature=base64.b64decode(signature),
            SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256'
        )
        is_valid = response.get('SignatureValid', None) if response else None
        if not is_valid:
            return None
        
        decoded = base64.b64decode(payload).decode()
        decoded = json.loads(decoded) if decoded else None
        return Payload.from_dict(decoded)