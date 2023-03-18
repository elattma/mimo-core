import { CfnOutput, Duration, Fn, Stack, StackProps } from "aws-cdk-lib";
import {
  ApiKeySourceType,
  Cors,
  IAuthorizer,
  IModel,
  JsonSchemaType,
  LambdaIntegration,
  RestApi,
  TokenAuthorizer,
} from "aws-cdk-lib/aws-apigateway";
import { GraphqlApi } from "aws-cdk-lib/aws-appsync";
import {
  Certificate,
  CertificateValidation,
} from "aws-cdk-lib/aws-certificatemanager";
import { ITable } from "aws-cdk-lib/aws-dynamodb";
import { Platform } from "aws-cdk-lib/aws-ecr-assets";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import {
  DockerImageCode,
  DockerImageFunction,
  Runtime,
} from "aws-cdk-lib/aws-lambda";
import { NodejsFunction } from "aws-cdk-lib/aws-lambda-nodejs";
import { HostedZone } from "aws-cdk-lib/aws-route53";
import { IBucket } from "aws-cdk-lib/aws-s3";
import { ISecret, Secret } from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import path = require("path");

export interface ApiStackProps extends StackProps {
  readonly stageId: string;
  readonly domainName: string;
  readonly mimoTable: ITable;
  readonly integrationsPath: string;
  readonly appsyncApi: GraphqlApi;
  readonly uploadItemBucket: IBucket;
}

interface LambdaParams {
  readonly method: string;
  readonly environment?: { [key: string]: string };
  readonly memorySize?: number;
  readonly timeout?: Duration;
}

export class ApiStack extends Stack {
  readonly api: RestApi;
  readonly authorizer: IAuthorizer;
  readonly integrationsSecret: ISecret;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);
    console.log(props.appsyncApi.graphqlUrl);

    const integrationSecretName = `${props.stageId}/Mimo/Integrations`;
    this.integrationsSecret = Secret.fromSecretNameV2(
      this,
      "integrations-secret",
      integrationSecretName
    );

    this.api = this.createRestApi(props.domainName);
    this.authorizer = this.createAuth0Authorizer(props.stageId);
    this.createDefaultApiKey();

    this.createChatRoutes(
      props.stageId,
      props.mimoTable,
      props.appsyncApi.graphqlUrl,
      props.uploadItemBucket
    );
    this.createIntegrationRoutes(
      props.stageId,
      props.mimoTable,
      props.integrationsPath
    );
    this.createItemRoutes(
      props.stageId,
      props.mimoTable,
      props.uploadItemBucket
    );
    this.createMysteryboxRoutes(
      props.stageId,
      props.mimoTable,
      props.uploadItemBucket
    );

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

  createMysteryboxRoutes = (
    stageId: string,
    mimoTable: ITable,
    uploadItemBucket: IBucket
  ) => {
    const mysterybox = this.api.root.addResource("mysterybox");
    const refreshMysteryboxHandler = this.getHandler({
      method: "mysterybox_post",
      environment: {
        STAGE: stageId,
        UPLOAD_ITEM_BUCKET: uploadItemBucket.bucketName,
        GRAPH_DB_URI: "neo4j+s://67eff9a1.databases.neo4j.io",
      },
      memorySize: 2048,
      timeout: Duration.minutes(10),
    });
    mimoTable.grantReadWriteData(refreshMysteryboxHandler);
    this.integrationsSecret.grantRead(refreshMysteryboxHandler);
    uploadItemBucket.grantRead(refreshMysteryboxHandler);

    const refreshMysteryboxResponseModel = this.api.addModel(
      "RefreshMysteryboxResponseModel",
      {
        contentType: "application/json",
        modelName: "RefreshMysteryboxResponse",
        schema: {
          type: JsonSchemaType.OBJECT,
          properties: {
            id: {
              type: JsonSchemaType.STRING,
            },
          },
        },
      }
    );

    mysterybox.addMethod(
      "POST",
      new LambdaIntegration(refreshMysteryboxHandler),
      {
        apiKeyRequired: true,
        authorizer: this.authorizer,
        methodResponses: [
          {
            statusCode: "200",
            responseModels: {
              "application/json": refreshMysteryboxResponseModel,
            },
            responseParameters: RESPONSE_PARAMS,
          },
        ],
      }
    );
  };

  createItemRoutes = (
    stageId: string,
    mimoTable: ITable,
    uploadItemBucket: IBucket
  ) => {
    const item = this.api.root.addResource("item");
    const getItemHandler = this.getHandler({
      method: "item_get",
      environment: {
        STAGE: stageId,
        UPLOAD_ITEM_BUCKET: uploadItemBucket.bucketName,
      },
      memorySize: 2048,
      timeout: Duration.seconds(30),
    });
    mimoTable.grantReadWriteData(getItemHandler);
    this.integrationsSecret.grantRead(getItemHandler);
    uploadItemBucket.grantRead(getItemHandler);

    const itemModel = this.api.addModel("ItemModel", {
      contentType: "application/json",
      modelName: "Item",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          id: {
            type: JsonSchemaType.STRING,
          },
          title: {
            type: JsonSchemaType.STRING,
          },
          link: {
            type: JsonSchemaType.STRING,
          },
          preview: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["id", "title", "link"],
      },
    });

    const itemResponseModel = this.api.addModel("ItemResponseModel", {
      contentType: "application/json",
      modelName: "ItemResponse",
      schema: {
        type: JsonSchemaType.ARRAY,
        items: {
          type: JsonSchemaType.OBJECT,
          properties: {
            integration: {
              type: JsonSchemaType.STRING,
            },
            icon: {
              type: JsonSchemaType.STRING,
            },
            items: {
              type: JsonSchemaType.ARRAY,
              items: {
                ref: getModelRef(this.api, itemModel),
              },
            },
            next_token: {
              type: JsonSchemaType.STRING,
            },
          },
        },
      },
    });

    item.addMethod("GET", new LambdaIntegration(getItemHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
      methodResponses: [
        {
          statusCode: "200",
          responseModels: {
            "application/json": itemResponseModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });

    const uploadItemHandler = this.getHandler({
      method: "item_post",
      environment: {
        STAGE: stageId,
        UPLOAD_ITEM_BUCKET: uploadItemBucket.bucketName,
      },
    });
    uploadItemBucket.grantPut(uploadItemHandler);

    const uploadItemRequestModel = this.api.addModel("UploadItemRequestModel", {
      contentType: "application/json",
      modelName: "UploadItemRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          contentType: {
            type: JsonSchemaType.STRING,
          },
          name: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["contentType"],
      },
    });

    const uploadItemResponseModel = this.api.addModel(
      "uploadItemResponseModel",
      {
        contentType: "application/json",
        modelName: "uploadItemResponse",
        schema: {
          type: JsonSchemaType.OBJECT,
          properties: {
            signedUrl: {
              type: JsonSchemaType.STRING,
            },
          },
          required: ["contentType"],
        },
      }
    );

    item.addMethod("POST", new LambdaIntegration(uploadItemHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
      requestModels: {
        "application/json": uploadItemRequestModel,
      },
      methodResponses: [
        {
          statusCode: "200",
          responseModels: {
            "application/json": uploadItemResponseModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });
  };

  createIntegrationRoutes = (
    stageId: string,
    mimoTable: ITable,
    integrationsPath: string
  ) => {
    // GET /integration
    const integration = this.api.root.addResource("integration");
    const getIntegrationHandler = this.getHandler({
      method: "integration_get",
      environment: {
        STAGE: stageId,
        INTEGRATIONS_PATH: integrationsPath,
      },
      timeout: Duration.seconds(5),
      memorySize: 512,
    });
    mimoTable.grantReadData(getIntegrationHandler);
    getIntegrationHandler.addToRolePolicy(
      new PolicyStatement({
        actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
        resources: [`*`],
      })
    );

    const integrationModel = this.api.addModel("IntegrationModel", {
      contentType: "application/json",
      modelName: "Integration",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          name: {
            type: JsonSchemaType.STRING,
          },
          description: {
            type: JsonSchemaType.STRING,
          },
          icon: {
            type: JsonSchemaType.STRING,
          },
          oauth2_link: {
            type: JsonSchemaType.STRING,
          },
          authorized: {
            type: JsonSchemaType.BOOLEAN,
            default: false,
          },
        },
        required: ["name", "description", "icon", "oauth2_link", "authorized"],
      },
    });

    const integrationListModel = this.api.addModel("IntegrationListModel", {
      contentType: "application/json",
      modelName: "IntegrationList",
      schema: {
        type: JsonSchemaType.ARRAY,
        items: {
          ref: getModelRef(this.api, integrationModel),
        },
      },
    });

    // TODO: figure out response for 1 specific integration
    integration.addMethod("GET", new LambdaIntegration(getIntegrationHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
      requestParameters: {
        "method.request.querystring.integration": false,
      },
      methodResponses: [
        {
          statusCode: "200",
          responseModels: {
            "application/json": integrationListModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });

    const authIntegrationHandler = this.getHandler({
      method: "integration_post",
      environment: {
        STAGE: stageId,
      },
      timeout: Duration.seconds(5),
      memorySize: 512,
    });
    mimoTable.grantWriteData(authIntegrationHandler);
    this.integrationsSecret.grantRead(authIntegrationHandler);

    const authIntegrationModel = this.api.addModel("AuthIntegrationModel", {
      contentType: "application/json",
      modelName: "AuthIntegration",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          id: {
            type: JsonSchemaType.STRING,
          },
          code: {
            type: JsonSchemaType.STRING,
          },
          redirect_uri: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["id", "code", "redirect_uri"],
      },
    });

    integration.addMethod(
      "POST",
      new LambdaIntegration(authIntegrationHandler),
      {
        apiKeyRequired: true,
        authorizer: this.authorizer,
        requestModels: {
          "application/json": authIntegrationModel,
        },
        methodResponses: [
          {
            statusCode: "200",
            responseParameters: RESPONSE_PARAMS,
          },
        ],
      }
    );
  };

  createChatRoutes = (
    stageId: string,
    mimoTable: ITable,
    graphqlUrl: string,
    uploadItemBucket: IBucket
  ) => {
    // POST /chat
    const chat = this.api.root.addResource("chat");
    const chatHandler = this.getHandler({
      method: "chat_post",
      environment: {
        STAGE: stageId,
        APPSYNC_ENDPOINT: graphqlUrl,
        UPLOAD_ITEM_BUCKET: uploadItemBucket.bucketName,
      },
      memorySize: 1024,
      timeout: Duration.seconds(20),
    });
    this.integrationsSecret.grantRead(chatHandler);
    mimoTable.grantReadWriteData(chatHandler);
    uploadItemBucket.grantRead(chatHandler);

    const chatModel = this.api.addModel("ChatModel", {
      contentType: "application/json",
      modelName: "Chat",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          id: {
            type: JsonSchemaType.STRING,
          },
          message: {
            type: JsonSchemaType.STRING,
          },
          author: {
            type: JsonSchemaType.STRING,
          },
          role: {
            type: JsonSchemaType.STRING,
            enum: ["user", "assistant"],
          },
          timestamp: {
            type: JsonSchemaType.INTEGER,
          },
        },
      },
    });

    const chatRequestModel = this.api.addModel("ChatRequestModel", {
      contentType: "application/json",
      modelName: "ChatRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          chat: {
            ref: getModelRef(this.api, chatModel),
          },
          items: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                integration: {
                  type: JsonSchemaType.STRING,
                },
                params: {
                  type: JsonSchemaType.ARRAY,
                  items: {
                    type: JsonSchemaType.OBJECT,
                    properties: {
                      id: {
                        type: JsonSchemaType.STRING,
                      },
                    },
                  },
                },
              },
            },
          },
        },
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
            "application/json": chatModel,
          },
          responseParameters: RESPONSE_PARAMS,
        },
      ],
    });

    // GET /chat
    const chatHistoryHandler = this.getHandler({
      method: "chat_get",
      environment: {
        STAGE: stageId,
        APPSYNC_ENDPOINT: graphqlUrl,
      },
      memorySize: 1024,
      timeout: Duration.seconds(20),
    });
    mimoTable.grantReadData(chatHistoryHandler);

    const chatHistoryModel = this.api.addModel("ChatHistoryModel", {
      contentType: "application/json",
      modelName: "ChatHistory",
      schema: {
        type: JsonSchemaType.ARRAY,
        items: {
          ref: getModelRef(this.api, chatModel),
        },
      },
    });

    chat.addMethod("GET", new LambdaIntegration(chatHistoryHandler), {
      apiKeyRequired: true,
      authorizer: this.authorizer,
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

  getHandler = (params: LambdaParams) => {
    const dockerfile = path.join(__dirname, "../../backend/");
    return new DockerImageFunction(this, `${params.method}-lambda`, {
      code: DockerImageCode.fromImageAsset(dockerfile, {
        file: "lambda.Dockerfile",
        cmd: [`app.handlers.${params.method}`],
        platform: Platform.LINUX_AMD64,
      }),
      timeout: params.timeout,
      memorySize: params.memorySize,
      environment: params.environment,
    });
  };
}

const RESPONSE_PARAMS = {
  "method.response.header.Content-Type": true,
  "method.response.header.Access-Control-Allow-Origin": true,
  "method.response.header.Access-Control-Allow-Credentials": true,
};

const getModelRef = (api: RestApi, model: IModel): string =>
  Fn.join("", [
    "https://apigateway.amazonaws.com/restapis/",
    api.restApiId,
    "/models/",
    model.modelId,
  ]);
