import json
import os

import boto3
from utils.responses import Errors, to_response_error, to_response_success

s3_client = None

def handler(event, context):
    global s3_client

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    upload_item_bucket: str = os.environ['UPLOAD_ITEM_BUCKET']
    body: str = event.get('body', None) if event else None
    body: dict = json.loads(body) if body else None
    content_type = body.get('contentType', None) if body else None
    name = body.get('name', None) if body else None

    if not (user and stage and upload_item_bucket and body and content_type and name):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not s3_client:
        s3_client = boto3.client('s3')
    
    signed_url = s3_client.generate_presigned_url(
        ClientMethod='put_object', 
        Params={
            'Bucket': upload_item_bucket,
            'Key': f'{user}/{name}',
            'ContentType': content_type      
        },
    )

    if not signed_url:
        return to_response_error(Errors.S3_ERROR.value)

    return to_response_success({
        'signedUrl': signed_url
    })