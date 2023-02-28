import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
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
import {
  Certificate,
  CertificateValidation,
} from "aws-cdk-lib/aws-certificatemanager";
import { ITable } from "aws-cdk-lib/aws-dynamodb";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
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
  readonly integrationsPath: string;
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
    this.createIntegrationRoutes(
      props.stageId,
      props.mimoTable,
      props.integrationsPath
    );
    this.createItemRoutes(props.stageId, props.mimoTable);

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

  createItemRoutes = (stageId: string, mimoTable: ITable) => {
    const item = this.api.root.addResource("item");
    const getItemHandler = new PythonFunction(this, "get-item-lambda", {
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      entry: path.join(__dirname, "../../backend/item"),
      index: "get.py",
      layers: this.commonPythonLayers,
      timeout: Duration.seconds(5),
      memorySize: 512,
      environment: {
        STAGE: stageId,
      },
      bundling: {
        assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
      },
    });
    mimoTable.grantReadWriteData(getItemHandler);
    this.integrationsSecret.grantRead(getItemHandler);

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
  };

  createIntegrationRoutes = (
    stageId: string,
    mimoTable: ITable,
    integrationsPath: string
  ) => {
    // GET /integration
    const integration = this.api.root.addResource("integration");
    const getIntegrationHandler = new PythonFunction(
      this,
      "get-integration-lambda",
      {
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        entry: path.join(__dirname, "../../backend/integration"),
        index: "get.py",
        layers: this.commonPythonLayers,
        timeout: Duration.seconds(5),
        memorySize: 512,
        environment: {
          STAGE: stageId,
          INTEGRATIONS_PATH: integrationsPath,
        },
        bundling: {
          assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
        },
      }
    );
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

    const authIntegrationHandler = new PythonFunction(
      this,
      "auth-integration-lambda",
      {
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        entry: path.join(__dirname, "../../backend/integration"),
        index: "post.py",
        layers: this.commonPythonLayers,
        timeout: Duration.seconds(5),
        memorySize: 512,
        environment: {
          STAGE: stageId,
        },
        bundling: {
          assetExcludes: ["**.venv**", "**.git**", "**.vscode**"],
        },
      }
    );
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
          items: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                integration: {
                  type: JsonSchemaType.STRING,
                },
                id: {
                  type: JsonSchemaType.STRING,
                },
              },
            },
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

const getModelRef = (api: RestApi, model: IModel): string =>
  Fn.join("", [
    "https://apigateway.amazonaws.com/restapis/",
    api.restApiId,
    "/models/",
    model.modelId,
  ]);
