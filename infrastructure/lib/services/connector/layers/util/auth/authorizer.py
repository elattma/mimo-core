from time import time

import requests
from shared.model import AuthType, TokenAuth, TokenOAuth2Strategy


class Authorizer:
    @staticmethod
    def token_oauth2(auth_strategy: TokenOAuth2Strategy, 
                     code: str, 
                     redirect_uri: str,
                     grant_type: str = 'authorization_code',
                     access_type: str = 'offline',
                     override_headers: dict = None) -> TokenAuth:
        if not (auth_strategy and code and redirect_uri):
            return None
        
        client_id = auth_strategy.client_id
        client_secret = auth_strategy.client_secret
        authorize_endpoint = auth_strategy.authorize_endpoint

        if not (client_id and client_secret and authorize_endpoint):
            return None

        data = {
            'grant_type': grant_type,
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'access_type': access_type,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if override_headers:
            headers.update(override_headers)

        response = requests.post(authorize_endpoint, data = data, headers = headers, auth = (client_id, client_secret))
        print(response)
        auth_response: dict = response.json() if response else None
        print(auth_response)
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
        
        if not access_token:
            return None

        print(access_token)
        print(refresh_token)
        print(timestamp)
        print(expiry_timestamp)
        return TokenAuth(
            type=AuthType.TOKEN_OAUTH2,
            access_token=access_token,
            refresh_token=refresh_token,
            timestamp=timestamp,
            expiry_timestamp=expiry_timestamp,
        )
    
    @staticmethod
    def refresh_token_oauth2(auth_strategy: TokenOAuth2Strategy, 
                             refresh_token: str,
                             grant_type: str = 'refresh_token',
                             access_type: str = 'offline',
                             override_headers: dict = None) -> TokenAuth:
        if not (auth_strategy and refresh_token):
            return None
        
        refresh_endpoint = auth_strategy.refresh_endpoint
        if not refresh_endpoint:
            return None
        
        data = {
            'grant_type': grant_type,
            'refresh_token': refresh_token,
            'access_type': access_type,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if override_headers:
            headers.update(override_headers)

        response = requests.post(refresh_endpoint, data = data, headers = headers)
        print(str(response))
        auth_response: dict = response.json() if response else None
        print(auth_response)
        access_token = auth_response.get('access_token', None) if auth_response else None
        refresh_token = auth_response.get('refresh_token', None) if auth_response else None
        expires_in = auth_response.get('expires_in', None) if auth_response else None
        timestamp = int(time())
        expiry_timestamp = expires_in + timestamp if expires_in else None
        if not expiry_timestamp:
            issued_at = auth_response.get('issued_at', None) if auth_response else None
            issued_at = int(issued_at) // 1000 if issued_at else None
            expiry_timestamp = issued_at + 86400 if issued_at else None

        if not access_token:
            return None
        
        print(access_token)
        print(refresh_token)
        print(timestamp)
        print(expiry_timestamp)
        return TokenAuth(
            type=AuthType.TOKEN_OAUTH2,
            access_token=access_token,
            refresh_token=refresh_token,
            timestamp=timestamp,
            expiry_timestamp=expiry_timestamp,
        )
