import os
import re
from typing import List, Mapping

import boto3
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.constants import Integration
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None
integrations: Mapping[str, Integration] = {}

def handler(event, context):
    global pc_db
    global integrations

    stage = os.environ['STAGE']
    integrations_path = os.environ['INTEGRATIONS_PATH']
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not stage or not integrations_path or not user:
        return to_response_error(Errors.MISSING_PARAMS)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    print(integrations)
    print(len(integrations))
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
            print(response)

            for parameter in response['Parameters']:
                id, key = re.search(r'/\w+/\w+/\w+/(\w+)/(\w+)', parameter.get('Name')).groups()
                value = parameter.get('Value')
                print(f'{id}, {key}, {value}')
                if id and key and value:
                    if not integrations.get(id):
                        integrations[id] = Integration(**{f"{key}": value})
                    else:
                        setattr(integrations.get(id), key, value)
                print(integrations)
            if next_token is None:
                break
    
    user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    response_integrations: List[Integration] = integrations.copy()
    for item in user_integration_items:
        integration = response_integrations.get(item.child.replace(KeyNamespaces.INTEGRATION.value, ''))
        if integration:
            response_integrations.get(integration).__dict__['authorized'] = True

    print(response_integrations.values())
    print(list(response_integrations.values()))
    return to_response_success([integration.__dict__ for integration in response_integrations.values()])