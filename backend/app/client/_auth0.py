import jwt
from app.client._secrets import Secrets
from jwt import PyJWKClient


class Auth0:
    _secrets: Secrets = None
    _jwk_client: PyJWKClient = None
    def __init__(self, stage: str):
        if not self._secrets:
            self._secrets = Secrets(stage, secret_id='Mimo/Integrations/Auth0')
        if not self._jwk_client:
            self._jwk_client = PyJWKClient(self._secrets.get('JWKS_URI'))
    
    def validated_get_user(self, auth_token: str) -> str:
        if not (auth_token and self._secrets and auth_token.startswith('Bearer ')):
            return None
        
        token = auth_token.split(' ')[1]
        audience = self._secrets.get('CLIENT_ID')
        signing_key = self._jwk_client.get_signing_key_from_jwt(token)
        decoded = jwt.decode(
            jwt=token, 
            key=signing_key.key, 
            algorithms=['RS256'], 
            audience=audience,
        )
        
        return decoded.get('sub', None) if decoded else None