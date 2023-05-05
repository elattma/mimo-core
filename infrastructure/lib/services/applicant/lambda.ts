import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Key, KeyUsage } from "aws-cdk-lib/aws-kms";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { MethodConfig } from "../../model";
import path = require("path");

export interface ApplicantStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class ApplicantStack extends Stack {
  readonly appMethods: MethodConfig[] = [];
  readonly authMethods: MethodConfig[] = [];

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

    const authKey = new Key(this, `auth-key`, {
      enableKeyRotation: true,
      description: `Auth key for ${props.stageId}`,
      keyUsage: KeyUsage.ENCRYPT_DECRYPT,
    });
    const authGetMethod = this.authGet(props.stageId, layers, authKey);
    this.authMethods.push(authGetMethod);
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
      use_authorizer: true,
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
      use_authorizer: true,
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
      use_authorizer: true,
    };
  };

  authGet = (
    stage: string,
    layers: PythonLayerVersion[],
    kmsKey: Key
  ): MethodConfig => {
    const handler = new PythonFunction(this, `auth-get-lambda`, {
      entry: path.join(__dirname, "auth"),
      index: "get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        KMS_KEY_ID: kmsKey.keyId,
        AUTH_ENDPOINT: "https://auth.mimo.team",
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });
    kmsKey.grantEncryptDecrypt(handler);

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
      use_authorizer: true,
    };
  };
}
