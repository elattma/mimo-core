# TODO: for now, place them on the waitlist
import os
from time import time

import boto3
from shared.response import Errors, to_response_error, to_response_success

_db = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    waitlist_table: str = os.getenv('WAITLIST_TABLE')

    if not (user and waitlist_table):
        return to_response_error(Errors.MISSING_PARAMS)
    
    if not _db:
        _db = boto3.resource('dynamodb').Table(waitlist_table)
    
    try:
        _db.put_item(
            Item={
                'email': user,
                'type': 'developer',
                'created_at': int(time()),
            }
        )
    except Exception as e:
        return to_response_error(Errors.DB_WRITE_FAILED)

    return to_response_success({
        'success': True
    })
