import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Key, KeySpec, KeyUsage } from "aws-cdk-lib/aws-kms";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface ApplicantStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class ApplicantStack extends Stack {
  readonly appMethods: MethodConfig[] = [];
  readonly authMethods: MethodConfig[] = [];
  readonly apiKeyMethods: MethodConfig[] = [];
  readonly developerMethods: MethodConfig[] = [];
  readonly v1AuthMethods: MethodConfig[] = [];
  readonly v1LibraryMethods: MethodConfig[] = [];

  constructor(scope: Construct, id: string, props: ApplicantStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
    const util = new PythonLayerVersion(this, `${props.stageId}-util-layer`, {
      entry: path.join(__dirname, `layers/util`),
      bundling: {
        assetExcludes: ["**.venv**", "**pycache**"],
      },
      compatibleRuntimes: [Runtime.PYTHON_3_9],
    });
    layers.push(util);
    const appPostMethod = this.appPost(props.stageId, layers);
    this.appMethods.push(appPostMethod);
    const appGetMethod = this.appGet(props.stageId, layers);
    this.appMethods.push(appGetMethod);
    const appDeleteMethod = this.appDelete(props.stageId, layers);
    this.appMethods.push(appDeleteMethod);

    const authKey = new Key(this, `signing-auth-key`, {
      description: `Auth key for ${props.stageId}`,
      keySpec: KeySpec.RSA_2048,
      keyUsage: KeyUsage.SIGN_VERIFY,
    });
    const authPostMethod = this.authPost(props.stageId, layers, authKey);
    this.authMethods.push(authPostMethod);

    const apiKeyPostMethod = this.apiKeyPost(props.stageId, layers);
    this.apiKeyMethods.push(apiKeyPostMethod);
    const apiKeyDeleteMethod = this.apiKeyDelete(props.stageId, layers);
    this.apiKeyMethods.push(apiKeyDeleteMethod);

    const developerGetMethod = this.developerGet(props.stageId, layers);
    this.developerMethods.push(developerGetMethod);
    const developerPatchMethod = this.developerPatch(props.stageId, layers);
    this.developerMethods.push(developerPatchMethod);
    const developerPostMethod = this.developerPost(props.stageId, layers);
    this.developerMethods.push(developerPostMethod);

    const v1AuthGetMethod = this.v1AuthGet(props.stageId, layers, authKey);
    this.v1AuthMethods.push(v1AuthGetMethod);
    const v1AuthDeleteMethod = this.v1AuthDelete(props.stageId, layers);
    this.v1AuthMethods.push(v1AuthDeleteMethod);

    const v1LibraryGetMethod = this.v1LibraryGet(props.stageId, layers);
    this.v1LibraryMethods.push(v1LibraryGetMethod);
  }

  appPost = (stage: string, layers: PythonLayerVersion[]): MethodConfig => {
    const handler = new PythonFunction(this, `app-post-lambda`, {
      entry: path.join(__dirname, "app"),
      index: "post.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AppPostRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          name: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["name"],
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AppPostResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          id: {
            type: JsonSchemaType.STRING,
          },
          name: {
            type: JsonSchemaType.STRING,
          },
          created_at: {
            type: JsonSchemaType.INTEGER,
          },
        },
        required: ["id", "name", "created_at"],
      },
    };

    return {
      name: "POST",
      handler: handler,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  appGet = (stage: string, layers: PythonLayerVersion[]): MethodConfig => {
    const handler = new PythonFunction(this, `app-get-lambda`, {
      entry: path.join(__dirname, "app"),
      index: "get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AppGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          apps: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                id: {
                  type: JsonSchemaType.STRING,
                },
                name: {
                  type: JsonSchemaType.STRING,
                },
                created_at: {
                  type: JsonSchemaType.INTEGER,
                },
              },
              required: ["id", "name", "created_at"],
            },
          },
          next_token: {
            type: JsonSchemaType.STRING,
          },
        },
      },
    };

    return {
      name: "GET",
      handler: handler,
      idResource: "app",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  appDelete = (stage: string, layers: PythonLayerVersion[]): MethodConfig => {
    const handler = new PythonFunction(this, `app-delete-lambda`, {
      entry: path.join(__dirname, "app"),
      index: "delete.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AppDeleteResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
      },
    };

    return {
      name: "DELETE",
      handler: handler,
      idResource: "app",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  authPost = (
    stage: string,
    layers: PythonLayerVersion[],
    kmsKey: Key
  ): MethodConfig => {
    const handler = new PythonFunction(this, `auth-post-lambda`, {
      entry: path.join(__dirname, "auth"),
      index: "post.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        KMS_KEY_ID: kmsKey.keyId,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });
    kmsKey.grant(handler, "kms:Verify");

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AuthPostRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          token: {
            type: JsonSchemaType.STRING,
          },
          library: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["token", "library"],
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AuthPostResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
      },
    };

    return {
      name: "POST",
      handler: handler,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  apiKeyPost = (stage: string, layers: PythonLayerVersion[]): MethodConfig => {
    const handler = new PythonFunction(this, `api-key-post-lambda`, {
      entry: path.join(__dirname, "api_key"),
      index: "post.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ApiKeyPostRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          app: {
            type: JsonSchemaType.STRING,
          },
          name: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["app", "name"],
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ApiKeyPostResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          apiKey: {
            type: JsonSchemaType.OBJECT,
            properties: {
              id: {
                type: JsonSchemaType.STRING,
              },
              name: {
                type: JsonSchemaType.STRING,
              },
              app: {
                type: JsonSchemaType.STRING,
              },
              owner: {
                type: JsonSchemaType.STRING,
              },
              created_at: {
                type: JsonSchemaType.INTEGER,
              },
            },
          },
        },
      },
    };

    return {
      name: "POST",
      handler: handler,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  apiKeyDelete = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `api-key-delete-lambda`, {
      entry: path.join(__dirname, "api_key"),
      index: "delete.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ApiKeyDeleteResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
      },
    };

    return {
      name: "DELETE",
      handler: handler,
      requestParameters: {
        "method.request.querystring.id": true,
        "method.request.querystring.app": true,
      },
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  developerGet = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `developer-get-lambda`, {
      entry: path.join(__dirname, "developer"),
      index: "get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        DEVELOPER_SECRET_PATH_PREFIX: `/${stage}/developer`,
        WAITLIST_TABLE: `mimo-${stage}-waitlist`,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "DeveloperGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          secret_key: {
            type: JsonSchemaType.STRING,
          },
        },
      },
    };

    return {
      name: "GET",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  developerPatch = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `developer-patch-lambda`, {
      entry: path.join(__dirname, "developer"),
      index: "patch.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        DEVELOPER_SECRET_PATH_PREFIX: `/${stage}/developer`,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "DeveloperPatchRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          regenerate_secret_key: {
            type: JsonSchemaType.BOOLEAN,
          },
        },
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "DeveloperPatchResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          secret_key: {
            type: JsonSchemaType.STRING,
          },
        },
      },
    };

    return {
      name: "PATCH",
      handler: handler,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  developerPost = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `developer-post-lambda`, {
      entry: path.join(__dirname, "developer"),
      index: "post.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        WAITLIST_TABLE: `mimo-${stage}-waitlist`,
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "DeveloperPostResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
      },
    };

    return {
      name: "POST",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  v1AuthGet = (
    stage: string,
    layers: PythonLayerVersion[],
    kmsKey: Key
  ): MethodConfig => {
    const handler = new PythonFunction(this, `v1-auth-get-lambda`, {
      entry: path.join(__dirname, "v1"),
      index: "auth_get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        KMS_KEY_ID: kmsKey.keyId,
        AUTH_ENDPOINT:
          stage === "beta"
            ? "https://www.mimo.team/auth"
            : "https://dev-frontend.mimo.team/auth",
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });
    kmsKey.grant(handler, "kms:Sign");

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AuthGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          authLink: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["authLink"],
      },
    };

    return {
      name: "GET",
      handler: handler,
      requestParameters: {
        "method.request.querystring.app": true,
      },
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.API_KEY,
    };
  };

  v1AuthDelete = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `v1-auth-delete-lambda`, {
      entry: path.join(__dirname, "v1"),
      index: "auth_delete.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AuthDeleteResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
        required: ["success"],
      },
    };

    return {
      name: "DELETE",
      handler: handler,
      requestParameters: {
        "method.request.querystring.app": true,
        "method.request.querystring.library": true,
      },
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.API_KEY,
    };
  };

  v1LibraryGet = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `v1-library-get-lambda`, {
      entry: path.join(__dirname, "v1"),
      index: "library_get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "AppLibraryGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          libraries: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                id: {
                  type: JsonSchemaType.STRING,
                },
                created_at: {
                  type: JsonSchemaType.NUMBER,
                },
              },
            },
            required: ["id", "created_at"],
          },
        },
      },
    };

    return {
      name: "GET",
      handler: handler,
      requestParameters: {
        "method.request.querystring.app": true,
      },
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.API_KEY,
    };
  };
}
