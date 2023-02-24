import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { CfnOutput, Duration, Stack, StackProps } from "aws-cdk-lib";
import {
  ApiKeySourceType,
  Cors,
  IAuthorizer,
  JsonSchemaType,
  LambdaIntegration,
  RestApi,
  TokenAuthorizer,
} from "aws-cdk-lib/aws-apigateway";
import {
  Certificate,
  CertificateValidation,
} from "aws-cdk-lib/aws-certificatemanager";
import { ITable } from "aws-cdk-lib/aws-dynamodb";
import { ILayerVersion, Runtime } from "aws-cdk-lib/aws-lambda";
import { NodejsFunction } from "aws-cdk-lib/aws-lambda-nodejs";
import { HostedZone } from "aws-cdk-lib/aws-route53";
import { ISecret, Secret } from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import path = require("path");

export interface ApiStackProps extends StackProps {
  readonly stageId: string;
  readonly domainName: string;
  readonly mimoTable: ITable;
}

export class ApiStack extends Stack {
  readonly api: RestApi;
  readonly authorizer: IAuthorizer;
  readonly commonPythonLayers: ILayerVersion[];
  readonly integrationsSecret: ISecret;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    const integrationSecretName = `${props.stageId}/Mimo/Integrations`;
    this.integrationsSecret = Secret.fromSecretNameV2(
      this,
      "integrations-secret",
      integrationSecretName
    );

    this.api = this.createRestApi(props.domainName);
    this.authorizer = this.createAuth0Authorizer(props.stageId);
    this.commonPythonLayers = this.createUtilsLayer();
    this.createDefaultApiKey();

    this.createChatRoutes(props.stageId, props.mimoTable);

    new CfnOutput(this, "api-gateway-id", {
      value: this.api.restApiId,
      exportName: "mimo-api-id",
    });
  }

  createRestApi = (domainName: string): RestApi => {
    const zone = HostedZone.fromLookup(this, "hosted-zone", {
      domainName: domainName,
    });

    const api = new RestApi(this, "mimo-api", {
      domainName: {
        domainName: `api.${domainName}`,
        certificate: new Certificate(this, "api-cert", {
          domainName: `api.${domainName}`,
          validation: CertificateValidation.fromDns(zone),
        }),
      },
      defaultCorsPreflightOptions: {
        allowHeaders: [
          "Content-Type",
          "X-Amz-Date",
          "Authorization",
          "X-Api-Key",
          "X-Amz-Security-Token",
        ],
        statusCode: 200,
        allowMethods: ["OPTIONS", "GET", "POST", "DELETE"],
        allowCredentials: true,
        allowOrigins: Cors.ALL_ORIGINS, // TODO: remove
      },
      apiKeySourceType: ApiKeySourceType.HEADER,
    });

    return api;
  };

  createDefaultApiKey = () => {
    const plan = this.api.addUsagePlan("usage-plan", {
      name: "test",
      throttle: {
        rateLimit: 10,
        burstLimit: 2,
      },
      apiStages: [
        {
          api: this.api,
          stage: this.api.deploymentStage,
        },
      ],
    });
    const key = this.api.addApiKey("test");
    plan.addApiKey(key);
  };

  createAuth0Authorizer = (stage: string): IAuthorizer => {
    const auth0SecretName = "beta/Mimo/Integrations/Auth0";
    const auth0Secret = Secret.fromSecretNameV2(
      this,
      "auth0-secret",
      auth0SecretName
    );
    const authorizerLambda = new NodejsFunction(this, "authorizer-lambda", {
      runtime: Runtime.NODEJS_18_X,
      handler: "handler",
      entry: path.join(__dirname, "authorizers/token.ts"),
      environment: {
        STAGE: stage,
      },
    });
    const authorizer = new TokenAuthorizer(this, "token-authorizer", {
      handler: authorizerLambda,
      authorizerName: "token_auth",
    });
    auth0Secret.grantRead(authorizerLambda);
    authorizer._attachToApi(this.api);
    return authorizer;
  };

  createUtilsLayer = (): ILayerVersion[] => {
    return [
      new PythonLayerVersion(this, "utils-layer", {
        entry: path.join(__dirname, "../../backend/python"),
        compatibleRuntimes: [Runtime.PYTHON_3_9],
        bundling: {
          assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
        },
      }),
    ];
  };

  createChatRoutes = (stageId: string, mimoTable: ITable) => {
    // POST /chat
    const chat = this.api.root.addResource("chat");
    const chatHandler = new PythonFunction(this, "chat-lambda", {
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      entry: path.join(__dirname, "../../backend/chat"),
      index: "post.py",
      layers: this.commonPythonLayers,
      timeout: Duration.seconds(20),
      memorySize: 2048,
      environment: {
        STAGE: stageId,
      },
      bundling: {
        assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
      },
    });
    this.integrationsSecret.grantRead(chatHandler);
    mimoTable.grantReadWriteData(chatHandler);

    const chatRequestModel = this.api.addModel("ChatRequestModel", {
      contentType: "application/json",
      modelName: "ChatRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          message: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["message"],
      },
    });

    const chatResponseModel = this.api.addModel("ChatResponseModel", {
      contentType: "application/json",
      modelName: "ChatResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          message: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["message"],
      },
    });

    chat.addMethod("POST", new LambdaIntegration(chatHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
      requestModels: {
        "application/json": chatRequestModel,
      },
      methodResponses: [
        {
          statusCode: "200",
          responseModels: {
            "application/json": chatResponseModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });

    // GET /chat
    const chatHistoryHandler = new PythonFunction(this, "chat-history-lambda", {
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      entry: path.join(__dirname, "../../backend/chat"),
      index: "get.py",
      layers: this.commonPythonLayers,
      timeout: Duration.seconds(10),
      memorySize: 512,
      environment: {
        STAGE: stageId,
      },
      bundling: {
        assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
      },
    });
    mimoTable.grantReadData(chatHistoryHandler);

    const chatHistoryModel = this.api.addModel("ChatHistoryModel", {
      contentType: "application/json",
      modelName: "ChatHistory",
      schema: {
        type: JsonSchemaType.ARRAY,
        items: {
          type: JsonSchemaType.OBJECT,
          properties: {
            author: {
              type: JsonSchemaType.STRING,
            },
            message: {
              type: JsonSchemaType.STRING,
            },
            timestamp: {
              type: JsonSchemaType.NUMBER,
            },
          },
          required: ["author", "message", "timestamp"],
        },
      },
    });

    chat.addMethod("GET", new LambdaIntegration(chatHistoryHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
      requestParameters: {
        "method.request.querystring.message": true,
      },
      methodResponses: [
        {
          statusCode: "200",
          responseModels: {
            "application/json": chatHistoryModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });
  };
}

const RESPONSE_PARAMS = {
  "method.response.header.Content-Type": true,
  "method.response.header.Access-Control-Allow-Origin": true,
  "method.response.header.Access-Control-Allow-Credentials": true,
};
