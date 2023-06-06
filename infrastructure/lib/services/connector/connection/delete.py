import os

from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, ParentChildDB

_db: ParentChildDB = None

def handler(event: dict, context):
    global _db

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    connection: str = path_parameters.get('connection', None) if path_parameters else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    library: str = query_string_parameters.get('library', None) if query_string_parameters else None
    stage: str = os.getenv('STAGE')

    if not (user and stage and connection and library):
        return to_response_error(Errors.MISSING_PARAMS)

    # first delete data from underlying data stores and only if those are successful, delete from the parent-child db
    # delete from s3 (if applicable)
    # delete from pinecone
    # delete from neo4j
    # delete from dynamo

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
    parent_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
    child_key = '{namespace}{connection}'.format(namespace=KeyNamespaces.CONNECTION.value, connection=connection)
    try:
        _db.delete(parent_key, child_key)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)
    return to_response_success({})