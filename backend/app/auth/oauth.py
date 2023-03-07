import json
from time import time

import requests
from app.auth.base import Auth


class OAuth(Auth):
    _TYPE = 'oauth'

    def __init__(self, client_id: str, client_secret: str, access_token: str = None, refresh_token: str = None, expiry_timestamp: int = None, authorize_endpoint: str = None, refresh_endpoint: str = None) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_timestamp = expiry_timestamp
        self.authorize_endpoint = authorize_endpoint
        self.refresh_endpoint = refresh_endpoint

    def validate(self) -> bool:
        return super().validate() and self.client_id and self.client_secret and self.access_token
    
    def authorize(self, params: dict) -> bool:
        if not (params and self.authorize_endpoint):
            return False
        
        code = params.get('code', None)
        redirect_uri = params.get('redirect_uri', None)
        if not (code and redirect_uri):
            return False
        
        override_data = params.get('override_data', {})
        override_headers = params.get('override_headers', {})

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': redirect_uri,
            'access_type': 'offline',
        }
        data.update(override_data)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        headers.update(override_headers)

        response = requests.post(self.authorize_endpoint, data = data, headers = headers, auth = (self.client_id, self.client_secret))

        auth_response = response.json() if response else None
        access_token = auth_response.get('access_token', None) if auth_response else None
        refresh_token = auth_response.get('refresh_token', None) if auth_response else None
        expires_in = auth_response.get('expires_in', None) if auth_response else None
        expiry_timestamp = expires_in + int(time()) if expires_in else None
        
        if not access_token:
            return False

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiry_timestamp = expiry_timestamp

        return True

    def refresh(self, params: dict = None) -> bool:
        if not self.refresh_endpoint:
            return False
        
        override_data = params.get('override_data', {}) if params else {}
        override_headers = params.get('override_headers', {}) if params else {}
        current_timestamp = int(time())
        if current_timestamp < self.expiry_timestamp:
            return True
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        data.update(override_data)

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        headers.update(override_headers)

        response = requests.post(self.refresh_endpoint, data=data, headers=headers, auth=(self.client_id, self.client_secret))

        auth_response = response.json() if response else None
        access_token: str = auth_response.get('access_token', None) if auth_response else None
        expires_in: str = auth_response.get('expires_in', None) if auth_response else None
        expiry_timestamp: int = int(expires_in) + current_timestamp if expires_in else None
        if not (access_token and expiry_timestamp):
            return False
        
        self.access_token = access_token
        self.expiry_timestamp = expiry_timestamp

        return True