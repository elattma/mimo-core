import { SecretsManager } from "@aws-sdk/client-secrets-manager";
import {
  APIGatewayAuthorizerCallback,
  APIGatewayAuthorizerResult,
  APIGatewayTokenAuthorizerEvent,
  Context,
} from "aws-lambda";
import * as jwt from "jsonwebtoken";

// Secrets
let secretStore: Map<string, string>;
const secretsClient = new SecretsManager({
  region: "us-east-1",
});

export const handler = async (
  event: APIGatewayTokenAuthorizerEvent,
  context: Context,
  callback: APIGatewayAuthorizerCallback
) => {
  if (!secretStore) {
    const response = await secretsClient.getSecretValue({
      SecretId: `${process.env.STAGE}/Mimo/Integrations/Auth0`,
    });

    const secret = response.SecretString
      ? response.SecretString
      : response.SecretBinary
      ? Buffer.from(response.SecretBinary.toString(), "base64").toString(
          "ascii"
        )
      : null;
    if (secret) {
      secretStore = new Map(Object.entries(JSON.parse(secret)));
    }
  }

  if (
    !secretStore ||
    !secretStore.has("CLIENT_ID") ||
    !secretStore.has("CLIENT_SECRET")
  ) {
    callback("Missing secrets");
  }

  const decodedToken = await decodeToken(event.authorizationToken);
  if (!decodedToken) {
    callback("Unauthorized");
  }

  callback(null, generatePolicy(decodedToken?.sub, "Allow", "*"));
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

const decodeToken = async (authorizationToken: string) => {
  if (
    !authorizationToken ||
    !authorizationToken.toLowerCase().match(/bearer (.+)/)
  ) {
    return null;
  }

  return jwt.verify(
    authorizationToken.split(" ")[1],
    secretStore.get("CLIENT_SECRET")?.split(";").join("\n") || "",
    {
      algorithms: ["RS256"],
      audience: secretStore.get("CLIENT_ID"),
    }
  );
};
