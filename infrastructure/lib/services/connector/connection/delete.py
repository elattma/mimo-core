import os
from typing import Dict

from airbyte.client import Airbyte
from shared.model import Integration
from shared.response import Errors, to_response_error, to_response_success
from state.dynamo import KeyNamespaces, LibraryConnectionItem, ParentChildDB
from state.params import SSM

_airbyte: Airbyte = None
_db: ParentChildDB = None
_integrations_dict: Dict[str, Integration] = None

def handler(event: dict, context):
    global _airbyte, _db, _integrations_dict

    airbyte_endpoint = os.getenv('AIRBYTE_ENDPOINT')
    stage = os.getenv('STAGE')
    integrations_path = os.getenv('INTEGRATIONS_PATH')
    if not (airbyte_endpoint and stage and integrations_path):
        raise Exception('missing env vars!')

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    path_parameters: dict = event.get('pathParameters', None) if event else None
    connection: str = path_parameters.get('connection', None) if path_parameters else None
    query_string_parameters: dict = event.get('queryStringParameters', None) if event else None
    library: str = query_string_parameters.get('library', None) if query_string_parameters else None

    if not (user and connection and library):
        return to_response_error(Errors.MISSING_PARAMS)

    if not _db:
        _db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    
    if not _integrations_dict:
        _ssm = SSM()
        integration_params = _ssm.load_params(integrations_path)
        _integrations_dict = {}
        for id, integration_params in integration_params.items():
            _integrations_dict[id] = Integration.from_dict(integration_params)
    parent_key = '{namespace}{library}'.format(namespace=KeyNamespaces.LIBRARY.value, library=library)
    child_key = '{namespace}{connection}'.format(namespace=KeyNamespaces.CONNECTION.value, connection=connection)
    integration: Integration = None
    try:
        item: LibraryConnectionItem = _db.get(parent_key, child_key)
        integration_id = item.connection.integration
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_READ_FAILED)
    finally:
        if not integration_id:
            return to_response_error(Errors.DB_READ_FAILED)
        integration = _integrations_dict.get(integration_id) if _integrations_dict else None
    
    if integration.airbyte_id:
        if not _airbyte:
            _airbyte = Airbyte(airbyte_endpoint)
        succeeded = _airbyte.delete(connection)
        if not succeeded:
            return to_response_error(Errors.DELETE_FAILED)

    # first delete data from underlying data stores and only if those are successful, delete from the parent-child db
    # delete from s3 (if applicable)
    
    # delete from pinecone
    # delete from neo4j
    # delete from dynamo
    # ...

    try:
        _db.delete(parent_key, child_key)
    except Exception as e:
        print(e)
        return to_response_error(Errors.DB_WRITE_FAILED)
    return to_response_success({
        'success': True,
    })