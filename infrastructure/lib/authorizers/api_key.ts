import { DynamoDB } from "@aws-sdk/client-dynamodb";
import { SSM } from "@aws-sdk/client-ssm";
import {
  APIGatewayAuthorizerCallback,
  APIGatewayAuthorizerResult,
  APIGatewayTokenAuthorizerEvent,
  Context,
} from "aws-lambda";

const ssmClient: SSM = new SSM({
  region: "us-east-1",
});

const dynamoClient: DynamoDB = new DynamoDB({
  region: "us-east-1",
});

export const handler = async (
  event: APIGatewayTokenAuthorizerEvent,
  context: Context,
  callback: APIGatewayAuthorizerCallback
) => {
  try {
    const authorization = event.authorizationToken;
    if (!authorization || !authorization.startsWith("Basic ")) {
      callback("Invalid Authorization header");
    }

    const encodedCredentials = authorization.substring(6);
    const decodedCredentials = Buffer.from(
      encodedCredentials,
      "base64"
    ).toString();
    const [apiKey, apiSecret] = decodedCredentials.split(":");
    if (!apiKey || !apiSecret) {
      callback("Invalid Authorization header format");
    }

    const items = await dynamoClient.query({
      TableName: process.env.TABLE_NAME,
      IndexName: "child-index",
      KeyConditionExpression: "child = :child",
      ExpressionAttributeValues: {
        ":child": {
          S: `API_KEY#${apiKey}`,
        },
      },
    });
    const key = items.Items?.[0];
    const owner = key?.["owner"]?.S;
    const ownerSanitized = owner?.replace(/[^a-zA-Z0-9._]/g, "-");
    if (!key) {
      callback("API Key not found!");
    } else {
      const response = await ssmClient.getParameter({
        Name: `${process.env.DEVELOPER_SECRET_PATH_PREFIX}/${ownerSanitized}/secret_key`,
        WithDecryption: true,
      });

      if (!response || !response.Parameter || !response.Parameter.Value) {
        callback("Not a valid developer!");
      }

      callback(null, generatePolicy(owner, "Allow", "*"));
    }
  } catch (error) {
    console.log(error);
    callback("Unauthorized");
  }
};

const generatePolicy = (
  principalId: any,
  effect: string,
  resource: string
): APIGatewayAuthorizerResult => {
  return {
    principalId:
      principalId && typeof principalId === "string" ? principalId : "",
    policyDocument: {
      Statement:
        !effect || !resource
          ? []
          : [
              {
                Action: "execute-api:Invoke",
                Effect: effect,
                Resource: resource,
              },
            ],
      Version: "2012-10-17",
    },
  };
};
