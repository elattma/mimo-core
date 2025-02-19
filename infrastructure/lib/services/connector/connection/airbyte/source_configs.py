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
        'channel_filter': []
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
    config['start_date'] = '2015-04-06T00:00:00Z'
    config['lookback_window'] = 100
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

def hubspot_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    hubspot_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'credentials': {
            'credentials_title': 'OAuth Credentials',
            'refresh_token': hubspot_auth.refresh_token,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        },
        'start_date': '2010-06-01T00:00:00Z',
    }

def asana_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    asana_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'credentials': {
            'option_title': 'OAuth Credentials',
            'refresh_token': asana_auth.refresh_token,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        },
        'start_date': '2010-06-01T00:00:00Z',
    }

def monday_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    monday_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'credentials': {
            'auth_type': 'oauth2.0',
            'access_token': monday_auth.access_token,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
            'subdomain': ''
        },
    }

def mailchimp_config(auth_strategy: AuthStrategy) -> Dict:
    if auth_strategy.get_type() != AuthType.TOKEN_OAUTH2:
        return None
    
    auth_strategy: TokenOAuth2Strategy = auth_strategy
    mailchimp_auth: TokenOAuth2 = auth_strategy._auth
    return {
        'credentials': {
            'auth_type': 'oauth2.0',
            'access_token': mailchimp_auth.access_token,
            'client_id': auth_strategy.client_id,
            'client_secret': auth_strategy.client_secret,
        },
    }

# TODO: add config to onboarding beyond auth strategy. should be able to configure anything you can in airbyte
# can have default values though
source_definition_id_to_config: Dict[str, Callable[[AuthStrategy], Dict]] = {
    'd8313939-3782-41b0-be29-b3ca20d8dd3a': intercom_config,
    'b117307c-14b6-41aa-9422-947e34922962': salesforce_config,
    'c2281cee-86f9-4a86-bb48-d23286b4c7bd': slack_config,
    '79c1aa37-dae3-42ae-b333-d1c105477715': zendesk_config,
    '4942d392-c7b5-4271-91f9-3b4f4e51eb3e': zoho_config,
    '6e00b415-b02e-4160-bf02-58176a0ae687': notion_config,
    '36c891d9-4bd9-43ac-bad2-10e12756272c': hubspot_config,
    'd0243522-dccf-4978-8ba0-37ed47a0bdbf': asana_config,
    '80a54ea2-9959-4040-aac1-eee42423ec9b': monday_config,
    'b03a9f3e-22a5-11eb-adc1-0242ac120002': mailchimp_config,
}