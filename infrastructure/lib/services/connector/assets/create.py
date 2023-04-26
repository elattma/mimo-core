# import json
# import os
# from time import time
# from typing import List

# from util.authorizer import Authorizer, TokenOAuth2Params
# from util.dynamo import KeyNamespaces, ParentChildDB, UserConnectionItem
# from util.model import Integration
# from util.response import Errors, to_response_error, to_response_success
# from util.secrets import Secrets

# _db: ParentChildDB = None
# _secrets: Secrets = None
# _integrations: List[Integration] = None

# def handler(event: dict, context):
#     global _db, _secrets

#     request_context: dict = event.get('requestContext', None) if event else None
#     authorizer: dict = request_context.get('authorizer', None) if request_context else None
#     user: str = authorizer.get('principalId', None) if authorizer else None
#     stage: str = os.getenv('STAGE')
#     body: str = event.get('body', None) if event else None
#     body: dict = json.loads(body) if body else None
#     token_oauth2: str = body.get('token_oauth2', None) if body else None

#     if not (user and stage and token_oauth2):
#         return to_response_error(Errors.MISSING_PARAMS.value)
    
#     if token_oauth2:
#         if not _secrets:
#             _secrets = Secrets(stage)
#         client_id = _secrets.get(f'{id}/CLIENT_ID')
#         client_secret = _secrets.get(f'{id}/CLIENT_SECRET')
#         params: TokenOAuth2Params = TokenOAuth2Params('', client_id, client_secret, token_oauth2, '')
#         Authorizer.token_oauth2()

#     if not succeeded:
#         return to_response_error(Errors.AUTH_FAILED.value)
    
#     if fetcher.auth.access_token:
#         if not db: 
#             db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
#         parent = f'{KeyNamespaces.USER.value}{user}'
#         child = f'{KeyNamespaces.INTEGRATION.value}{id}'
#         try:
#             print(fetcher.auth)
#             db.write([UserIntegrationItem(parent, child, fetcher.auth.access_token, fetcher.auth.refresh_token, int(time()), fetcher.auth.expiry_timestamp)])
#         except Exception as e:
#             print(e)
#             return to_response_error(Errors.DB_WRITE_FAILED.value)

#     return to_response_success({})
