import json
import os
import re
from typing import List, Mapping

import boto3
from db.pc import KeyNamespaces, ParentChildDB, UserIntegrationItem
from utils.constants import Integration

pc_db: ParentChildDB = None
integrations: Mapping[Integration] = None

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
}

def handler(event, context):
    global pc_db
    global integrations

    stage = os.environ['STAGE']
    integrations_path = os.environ['INTEGRATIONS_PATH']
    user = event['requestContext']['authorizer']['principalId'] if event and event['requestContext'] and event['requestContext']['authorizer'] else None

    if not stage or not integrations_path or not user:
        return {
            "statusCode": 400,
            "headers": HEADERS,
        }

    if pc_db is None:
        pc_db = ParentChildDB("mimo-{stage}-pc".format(stage=stage))

    if integrations is None:
        ssm_client = boto3.client("ssm")
        integrations: Mapping[Integration] = {}
        next_token = None
        while True:
            response = ssm_client.get_parameters_by_path(
                Path=integrations_path,
                Recursive=True,
                NextToken=next_token
            )
            next_token = response.get("NextToken")

            for parameter in response["Parameters"]:
                _, id, key = re.search(r"/\/\w+\/\w+\/\w+\/(\w+)\/(\w+)/", parameter.get("Name")).groups()
                value = parameter.get("Value")
                print(f"{id}, {key}, {value}")
                if id and key and value:
                    if id not in integrations:
                        integrations.update({
                            "{id}": Integration(**{key: value})
                        })
                    else:
                        integrations.get(id).__dict__[key] = value

            if next_token is None:
                break
    
    user_integration_items: List[UserIntegrationItem] = pc_db.query("{namespace}{user}".format(namespace=KeyNamespaces.USER.value, user=user), child_namespace=KeyNamespaces.INTEGRATION.value, limit=100)
    response_integrations = integrations.copy()
    for item in user_integration_items:
        integration = response_integrations.get(item.child.replace(KeyNamespaces.INTEGRATION.value, ""))
        if integration:
            response_integrations.get(integration).__dict__["authorized"] = True

    return {
        "statusCode": 200,
        "headers": HEADERS,
        "body": json.dumps(response_integrations.values())
    }