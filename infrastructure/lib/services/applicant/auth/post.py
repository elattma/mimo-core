import json
import os
from time import time
from typing import List

from keys.kms import KMS
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import (KeyNamespaces, LibraryAppItem, ParentChildDB,
                          ParentChildItem)

_db: ParentChildDB = None
_kms: KMS = None

def handler(event: dict, context):
    global _db, _kms

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    token: str = body.get('token', None) if body else None
    kms_key_id: str = os.getenv('KMS_KEY_ID')
    stage: str = os.getenv('STAGE')

    if not (user and stage and kms_key_id and token):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user)
    child_namespace = KeyNamespaces.LIBRARY.value
    library: str = None
    try: 
        items: List[ParentChildItem] = _db.query(parent_key, child_namespace)
        if not items:
            return to_response_error(Errors.LIBRARY_NOT_FOUND)
        library = items[0].get_raw_child()
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)    
    if not library:
        return to_response_error(Errors.LIBRARY_NOT_FOUND)

    if not _kms:
        _kms = KMS()
    payload = _kms.verify(token=token, key_id=kms_key_id)
    if not payload:
        return to_response_error(Errors.INVALID_TOKEN)
    
    try:
        parent_key = '{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=payload.user)
        child_key = '{namespace}{app}'.format(namespace=KeyNamespaces.APP.value, app=payload.app.id)
        is_valid_user_app = _db.exists(parent_key, child_key)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    if not is_valid_user_app:
        return to_response_error(Errors.APP_NOT_FOUND)
    
    now_timestamp = int(time())
    if now_timestamp > payload.expiration:
        return to_response_error(Errors.TOKEN_EXPIRED)
    try:
        library_app_item: LibraryAppItem = LibraryAppItem(
            parent='{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library),
            app_id=payload.app.id,
            timestamp=now_timestamp
        )
        _db.write([library_app_item])
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)
    return to_response_success({
        'success': True
    })
