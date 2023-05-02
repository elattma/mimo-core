#!/bin/bash

# Loop through each line in the .env file
while IFS= read -r line; do
    # Split the line by the equals sign to get the key and value
    key=${line%=*}
    value=${line#*=}
    
    # Write the key-value pair to Parameter Store as a secure string
    aws ssm put-parameter --profile mimo \
        --name "${key}" \
        --value "${value}" \
        --type SecureString \
        --overwrite
done < secrets.env