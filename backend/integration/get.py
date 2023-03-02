import os
import re
from typing import List, Mapping

import boto3
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.constants import Integration
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
integrations: Mapping[str, Integration] = {}

def handler(event: dict, context):
    global pc_db
    global integrations

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    integrations_path: str = os.environ['INTEGRATIONS_PATH']

    if not user or not stage or not integrations_path:
        return to_response_error(Errors.MISSING_PARAMS.value)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    if not integrations or len(integrations) < 1:
        ssm_client = boto3.client('ssm')
        next_token = None
        while True:
            response = ssm_client.get_parameters_by_path(
                Path=integrations_path,
                Recursive=True,
                **({'NextToken': next_token} if next_token is not None else {})
            )
            next_token = response.get('NextToken')

            for parameter in response['Parameters']:
                id, key = re.search(r'/\w+/\w+/\w+/(\w+)/(\w+)', parameter.get('Name')).groups()
                value = parameter.get('Value')
                if id and key and value:
                    if not integrations.get(id):
                        integrations[id] = Integration(**{f"{key}": value})
                    else:
                        setattr(integrations.get(id), key, value)
            if next_token is None:
                break
    
    user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    response_integrations: Mapping[str, Integration] = integrations.copy()
    for item in user_integration_items:
        integration = response_integrations[item.get_raw_child()]
        if integration:
            integration.authorized = True

    return to_response_success([integration.__dict__ for integration in response_integrations.values()])