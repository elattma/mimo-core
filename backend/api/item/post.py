import json
import os

# from fetcher.base import Fetcher
# from fetcher.upload_docs import Upload
from aws.response import Errors, to_response_error, to_response_success


def handler(event: dict, context):
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

    # upload: Upload = Fetcher.create('upload', {
    #     'bucket': upload_item_bucket,
    #     'prefix': user
    # })
    # signed_url = upload.generate_presigned_url(content_type=content_type, name=name)

    # if not signed_url:
    #     return to_response_error(Errors.S3_ERROR.value)

    # return to_response_success({
    #     'signedUrl': signed_url
    # })

    return to_response_success()