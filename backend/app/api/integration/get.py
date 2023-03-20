import os
from typing import List, Mapping

from app.api.util.response import (Errors, to_response_error,
                                   to_response_success)
from app.client._ssm import SSM, Integration
from app.client.parent_child_db import (KeyNamespaces, ParentChildDB,
                                        UserIntegrationItem)

db: ParentChildDB = None
ssm: SSM = None

def handler(event: dict, context):
    global db, ssm

    request_context: dict = event.get('requestContext', None) if event else None
    authorizer: dict = request_context.get('authorizer', None) if request_context else None
    user: str = authorizer.get('principalId', None) if authorizer else None
    stage: str = os.environ['STAGE']
    integrations_path: str = os.environ['INTEGRATIONS_PATH']

    if not (user and stage and integrations_path):
        return to_response_error(Errors.MISSING_PARAMS.value)

    if not db:
        db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))
    if not ssm:
        ssm = SSM(path=integrations_path)
    
    user_integration_items: List[UserIntegrationItem] = db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    response_integrations: Mapping[str, Integration] = ssm.integrations.copy()
    for item in user_integration_items:
        integration = response_integrations[item.get_raw_child()]
        if integration:
            integration.authorized = True

    return to_response_success([integration.__dict__ for integration in response_integrations.values()])