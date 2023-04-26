from dataclasses import dataclass
from time import time

import requests
from model import AuthType, TokenOAuth2


@dataclass
class TokenOAuth2Params:
    authorize_endpoint: str
    client_id: str
    client_secret: str
    code: str
    redirect_uri: str
    override_data: dict = None
    override_headers: dict = None

class Authorizer:
    @staticmethod
    def token_oauth2(params: TokenOAuth2Params) -> TokenOAuth2:
        if not params:
            return False
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': params.client_id,
            'client_secret': params.client_secret,
            'code': params.code,
            'redirect_uri': params.redirect_uri,
            'access_type': 'offline',
        }
        if params.override_data:
            data.update(params.override_data)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if params.override_headers:
            headers.update(params.override_headers)

        response = requests.post(params.authorize_endpoint, data = data, headers = headers, auth = (params.client_id, params.client_secret))
        auth_response = response.json() if response else None
        access_token = auth_response.get('access_token', None) if auth_response else None
        refresh_token = auth_response.get('refresh_token', None) if auth_response else None
        expires_in = auth_response.get('expires_in', None) if auth_response else None
        timestamp = int(time())
        expiry_timestamp = expires_in + timestamp if expires_in else None
        if not expiry_timestamp:
            #TODO: hack for salesforce, generalize this. 1 day expiration, issued_at in ms
            issued_at = auth_response.get('issued_at', None) if auth_response else None
            issued_at = int(issued_at) // 1000 if issued_at else None
            expiry_timestamp = issued_at + 86400 if issued_at else None
        
        auth = TokenOAuth2(
            type=AuthType.TOKEN_OAUTH2.value,
            access_token=access_token,
            refresh_token=refresh_token,
            timestamp=timestamp,
            expiry_timestamp=expiry_timestamp,
        )
        return auth
