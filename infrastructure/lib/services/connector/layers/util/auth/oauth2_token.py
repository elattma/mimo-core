from dataclasses import dataclass
from time import time

import requests
from auth.base import Auth, AuthStrategy, AuthType


@dataclass
class TokenOAuth2(Auth):
    refresh_token: str
    expiry_timestamp: int
    access_token: str

    def is_valid(self):
        return self.timestamp and ((self.refresh_token and self.expiry_timestamp) or self.access_token)
    
    def as_dict(self):
        return {
            'type': AuthType.TOKEN_OAUTH2.value,
            'timestamp': self.timestamp,
            'refresh_token': self.refresh_token,
            'expiry_timestamp': self.expiry_timestamp,
            'access_token': self.access_token
        }

@dataclass
class TokenOAuth2Strategy(AuthStrategy):
    oauth2_link: str
    authorize_endpoint: str
    client_id: str
    client_secret: str
    refresh_endpoint: str = None

    @classmethod
    def get_type(cls) -> AuthType:
        return AuthType.TOKEN_OAUTH2
    
    def get_params(self):
        return {
            'oauth2_link': self.oauth2_link,
        }
    
    @classmethod
    def auth_from_params(cls,
                         timestamp: int,
                         refresh_token: str,
                         expiry_timestamp: int,
                         access_token: str = None) -> TokenOAuth2:
        return TokenOAuth2(
            timestamp=int(timestamp) if timestamp else None, 
            refresh_token=refresh_token, 
            expiry_timestamp=int(expiry_timestamp) if expiry_timestamp else None,
            access_token=access_token
        )
    
    def auth(self, 
             grant_type: str = 'refresh_token',
             code: str = None, 
             redirect_uri: str = None,
             refresh_token: str = None,
             access_token: str = None,
             access_type: str = 'offline',
             override_headers: dict = None,
             **kwargs) -> TokenOAuth2:
        if grant_type == 'authorization_code':
            self._auth = self._code_auth(
                code=code,
                redirect_uri=redirect_uri,
                access_type=access_type,
                override_headers=override_headers
            )
            return self._auth
        if grant_type == 'refresh_token':
            if not refresh_token and access_token:
                return self._auth
            self._auth = self._refresh_auth(
                refresh_token=refresh_token,
                override_headers=override_headers
            )
            return self._auth

    def _code_auth(self, 
                   code: str = None, 
                   redirect_uri: str = None,
                   access_type: str = 'offline',
                   override_headers: dict = None) -> TokenOAuth2:
        if not (code and redirect_uri and self.authorize_endpoint and self.client_id and self.client_secret):
            raise Exception('Missing required parameters for code auth')

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'access_type': access_type,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if override_headers:
            headers.update(override_headers)

        response = requests.post(self.authorize_endpoint, data = data, headers = headers, auth = (self.client_id, self.client_secret))
        print(f'code auth response: {str(response) if response else "empty"}')
        auth_response: dict = response.json() if response else None
        print(f'auth response json: {auth_response}')
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
        
        if not (refresh_token and expiry_timestamp) and not access_token:
            raise Exception('Invalid auth response')

        return TokenOAuth2(
            timestamp=timestamp,
            refresh_token=refresh_token,
            expiry_timestamp=expiry_timestamp,
            access_token=access_token
        )
    
    def _refresh_auth(self,
                      refresh_token: str,
                      access_type: str = 'offline',
                      override_headers: dict = None) -> TokenOAuth2:
        if not (refresh_token and self.refresh_endpoint):
            raise Exception('Invalid refresh params')
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'access_type': access_type,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        if override_headers:
            headers.update(override_headers)

        response = requests.post(self.refresh_endpoint, data = data, headers = headers)
        print(f'code auth response: {str(response) if response else "empty"}')
        auth_response: dict = response.json() if response else None
        print(f'auth response json: {auth_response}')
        access_token = auth_response.get('access_token', None) if auth_response else None
        expires_in = auth_response.get('expires_in', None) if auth_response else None
        timestamp = int(time())
        expiry_timestamp = expires_in + timestamp if expires_in else None
        if not expiry_timestamp:
            issued_at = auth_response.get('issued_at', None) if auth_response else None
            issued_at = int(issued_at) // 1000 if issued_at else None
            expiry_timestamp = issued_at + 86400 if issued_at else None

        if not (access_token and expiry_timestamp):
            raise Exception('Invalid refresh response')

        return TokenOAuth2(
            timestamp=timestamp,
            refresh_token=refresh_token,
            expiry_timestamp=expiry_timestamp,
            access_token=access_token,
        )
