import boto3

sqs = boto3.client('sqs')
secrets = boto3.client('secretsmanager')
