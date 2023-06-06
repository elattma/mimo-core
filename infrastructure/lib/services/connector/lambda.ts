import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface ConnectorStackProps extends StackProps {
  readonly stageId: string;
}

export class ConnectorStack extends Stack {
  readonly methods: MethodConfig[] = [];
  readonly integrationMethods: MethodConfig[] = [];
  readonly libraryMethods: MethodConfig[] = [];
  readonly layers: PythonLayerVersion[] = [];

  constructor(scope: Construct, id: string, props: ConnectorStackProps) {
    super(scope, id, props);

    const util = new PythonLayerVersion(this, `${props.stageId}-util-layer`, {
      entry: path.join(__dirname, `layers/util`),
      bundling: {
        assetExcludes: ["**.venv**", "**pycache**"],
      },
      compatibleRuntimes: [Runtime.PYTHON_3_9],
    });
    this.layers.push(util);
    const createMethod = this.connectionPost(props.stageId);
    this.methods.push(createMethod);
    const getMethod = this.connectionGet(props.stageId);
    this.methods.push(getMethod);
    const deleteMethod = this.connectionDelete(props.stageId);
    this.methods.push(deleteMethod);

    const integrationsMethod = this.integrationGet(props.stageId);
    this.integrationMethods.push(integrationsMethod);

    const libraryMethod = this.libraryGet(props.stageId);
    this.libraryMethods.push(libraryMethod);
  }

  connectionPost = (stage: string): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-create-lambda`,
      {
        entry: path.join(__dirname, "connection"),
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
        layers: this.layers,
      }
    );

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorGenerateRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          library: {
            type: JsonSchemaType.STRING,
          },
          integration: {
            type: JsonSchemaType.STRING,
          },
          name: {
            type: JsonSchemaType.STRING,
          },
          auth_strategy: {
            type: JsonSchemaType.OBJECT,
          },
        },
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorGenerateResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          connection: {
            type: JsonSchemaType.OBJECT,
            properties: {
              id: {
                type: JsonSchemaType.STRING,
              },
              name: {
                type: JsonSchemaType.STRING,
              },
              integration: {
                type: JsonSchemaType.STRING,
              },
              created_at: {
                type: JsonSchemaType.STRING,
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

  connectionGet = (stage: string): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-connector-get-lambda`, {
      entry: path.join(__dirname, "connection"),
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
      layers: this.layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          connections: {
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
                integration: {
                  type: JsonSchemaType.STRING,
                },
                created_at: {
                  type: JsonSchemaType.STRING,
                },
              },
            },
            required: ["id", "name", "integration", "created_at"],
          },
        },
      },
    };

    return {
      name: "GET",
      handler: handler,
      idResource: "connection",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  connectionDelete = (stage: string): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-delete-lambda`,
      {
        entry: path.join(__dirname, "connection"),
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
        layers: this.layers,
      }
    );

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorDeleteResponse",
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
      idResource: "connection",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  integrationGet = (stage: string): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-integrations-lambda`,
      {
        entry: path.join(__dirname, "integration"),
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
          assetExcludes: ["**.venv**"],
        },
        layers: this.layers,
      }
    );

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorIntegrationsResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          integrations: {
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
                description: {
                  type: JsonSchemaType.STRING,
                },
                icon: {
                  type: JsonSchemaType.STRING,
                },
                oauth2_link: {
                  type: JsonSchemaType.STRING,
                },
              },
              required: ["id", "name", "description", "icon", "oauth2_link"],
            },
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

  libraryGet = (stage: string): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-library-lambda`,
      {
        entry: path.join(__dirname, "library"),
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
          assetExcludes: ["**.venv**"],
        },
        layers: this.layers,
      }
    );

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "Library",
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
      idResource: "library",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };
}
