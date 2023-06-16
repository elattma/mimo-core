import os

import boto3
from shared.response import Errors, to_response_error, to_response_success

_s3 = None

def handler(event: dict, context):
    global _s3

    stage = os.getenv('STAGE')
    upload_bucket = os.getenv('UPLOAD_BUCKET')
    if not (stage and upload_bucket):
        raise Exception('missing env vars!')

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    library: str = query_string_parameters.get('library', None) if query_string_parameters else None
    file_name: str = query_string_parameters.get('file_name', None) if query_string_parameters else None

    if not (user and library and file_name):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _s3:
        _s3 = boto3.client('s3')

    signed_url = _s3.generate_presigned_url(
        ClientMethod='put_object',
        Params={
            'Bucket': upload_bucket,
            'Key': f'{library}/{file_name}',
        },
        ExpiresIn=600
    )
    if not signed_url:
        return to_response_error(Errors.S3_UPLOAD_FAILED)

    return to_response_success({
        'signed_url': signed_url,
    })
