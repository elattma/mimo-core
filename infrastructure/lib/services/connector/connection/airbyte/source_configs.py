from typing import Callable, Dict

from auth.api_key import ApiKeyStrategy
from auth.base import AuthStrategy
from auth.oauth2_token import TokenOAuth2, TokenOAuth2Strategy
from shared.model import AuthType


def intercom_config(auth_strategy: AuthStrategy) -> Dict:
    intercom_auth = auth_strategy._auth.as_dict()
    access_token = intercom_auth.get('access_token', None)
    if not access_token:
        return None
    
    return {
        'access_token': access_token,
        'start_date': '2000-01-01T00:00:00Z'
    }

def salesforce_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    auth: TokenOAuth2 = auth_strategy._auth
    if not auth.refresh_token:
        return None

    return {
        'client_id': auth_strategy.client_id,
        'client_secret': auth_strategy.client_secret,
        'refresh_token': auth.refresh_token,
        'start_date': '2000-01-01T00:00:00Z',
        'is_sandbox': False,
        'auth_type': 'Client',
    }

def slack_config(auth_strategy: AuthStrategy) -> Dict:
    config = {
        'join_channels': True,
    }
    credentials = None
    if auth_strategy.get_type() == AuthType.TOKEN_OAUTH2:
        auth_strategy: TokenOAuth2Strategy = auth_strategy
        credentials = {
            'option_title': 'Default OAuth2.0 authorization',
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        }
        slack_auth = auth_strategy._auth.as_dict()
        access_token = slack_auth.get('access_token', None)
        if not access_token:
            return None
        credentials['access_token'] = access_token
    elif auth_strategy.get_type() == AuthType.API_KEY:
        auth_strategy: ApiKeyStrategy = auth_strategy
        slack_auth = auth_strategy._auth.as_dict()
        key = slack_auth.get('key', None)
        if not key:
            return None
        credentials = {
            'option_title': 'API Token Credentials',
            'api_token': key,
        }
    
    if not credentials:
        return None

    config['start_date'] = '2000-01-01T00:00:00Z'
    config['lookback_window'] = 10000
    config['credentials'] = credentials
    return config

def zendesk_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    zendesk_auth: TokenOAuth2 = auth_strategy._auth

    return {
        'ignore_pagination': False,
        'credentials': {
            'credentials': 'oauth2.0',
            'access_token': zendesk_auth.access_token,
        },
        'start_date': '2000-01-01T00:00:00Z',
        'subdomain': 'd3v-mimo3158'
    }

def zoho_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    zoho_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'edition': 'Free',
        'client_id': auth_strategy.client_id,
        'client_secret': auth_strategy.client_secret,
        'dc_region': 'US',
        'environment': 'Production',
        'refresh_token': zoho_auth.refresh_token
    }

def notion_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    notion_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'credentials': {
            'auth_type': 'OAuth2.0',
            'access_token': notion_auth.access_token,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        },
        'start_date': '2000-06-01T00:00:00.000Z',
    }


# TODO: add config to onboarding beyond auth strategy. should be able to configure anything you can in airbyte
# can have default values though
source_definition_id_to_config: Dict[str, Callable[[AuthStrategy], Dict]] = {
    'd8313939-3782-41b0-be29-b3ca20d8dd3a': intercom_config,
    'b117307c-14b6-41aa-9422-947e34922962': salesforce_config,
    'c2281cee-86f9-4a86-bb48-d23286b4c7bd': slack_config,
    '79c1aa37-dae3-42ae-b333-d1c105477715': zendesk_config,
    '4942d392-c7b5-4271-91f9-3b4f4e51eb3e': zoho_config,
    'b1c1b2a0-5b0a-4b0a-9b0a-6b0a6b0a6b0a': notion_config
}