#!/bin/bash

echo "Please enter the environment name (e.g. dev, beta):"
read env

echo "Please enter the user id:"
read userid

declare -A env_api_map
env_api_map["dev"]="f3awvrk6y6"
env_api_map["beta"]="hh0m5ohg5f"

userid_sanitized=$(echo "$owner" | tr -c '[:alnum:]._' '-')
secret_key=$(uuidgen)
aws ssm put-parameter --profile mimo \
    --name "/$env/developer/$userid_sanitized/secret_key" \
    --value $(secret_key) \
    --type "SecureString"

api_key_value=$(uuidgen)
api_key=$(aws apigateway create-api-key --profile mimo --name $(userid) --value $(api_key_value) --enabled --output text)
aws apigateway create-usage-plan-key --profile mimo --usage-plan-id ${env_api_map[$env]} --key-type API_KEY --key-id $api_key
aws apigateway update-rest-api  --profile mimo --rest-api-id ${env_api_map[$env]} --patch-operations op=add,path=/apiKeys, value="$api_key"