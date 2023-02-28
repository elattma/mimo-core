# id title icon link optional(preview)import os
import os
from typing import List

import boto3
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.constants import Integration
from utils.responses import Errors, to_response_error, to_response_success

pc_db: ParentChildDB = None

def handler(event, context):
    global pc_db
    global integrations

    stage = os.environ['STAGE']
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not stage or not user:
        return to_response_error(Errors.MISSING_PARAMS)

    if pc_db is None:
        pc_db = ParentChildDB('mimo-{stage}-pc'.format(stage=stage))

    user_integration_items: List[UserIntegrationItem] = pc_db.query('{namespace}{user}'.format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, Limit=100)
    print(user_integration_items)
    for integration in user_integration_items:
        if integration.child.endswith('google'):
            # call google api to get data
            print('google')

    return to_response_success(list())