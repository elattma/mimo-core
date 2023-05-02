import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { MethodConfig } from "../../model";
import path = require("path");

export interface ConnectorStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class ConnectorStack extends Stack {
  readonly methods: MethodConfig[] = [];
  readonly integrationMethods: MethodConfig[] = [];
  readonly integrationModel: ModelOptions;
  readonly connectionModel: ModelOptions;

  constructor(scope: Construct, id: string, props: ConnectorStackProps) {
    super(scope, id, props);

    this.integrationModel = {
      contentType: "application/json",
      modelName: "Integration",
      schema: {
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
          auth_strategies: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
            },
          },
        },
        required: ["id", "name", "description", "icon", "auth_strategies"],
      },
    };

    this.connectionModel = {
      contentType: "application/json",
      modelName: "Connection",
      schema: {
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
          ingested_at: {
            type: JsonSchemaType.STRING,
          },
        },
      },
    };

    const layers: PythonLayerVersion[] = [];
    const util = new PythonLayerVersion(this, `${props.stageId}-util-layer`, {
      entry: path.join(__dirname, `layers/util`),
      bundling: {
        assetExcludes: ["**.venv**", "**pycache**"],
      },
      compatibleRuntimes: [Runtime.PYTHON_3_9],
    });
    layers.push(util);
    const createMethod = this.connectionPost(props.stageId, layers);
    this.methods.push(createMethod);
    const getMethod = this.connectionGet(props.stageId, layers);
    this.methods.push(getMethod);
    const deleteMethod = this.connectionDelete(props.stageId, layers);
    this.methods.push(deleteMethod);

    const integrationsMethod = this.integrationGet(props.stageId, layers);
    this.integrationMethods.push(integrationsMethod);
  }

  connectionPost = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
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
        layers: layers,
      }
    );

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ConnectorGenerateRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          name: {
            type: JsonSchemaType.STRING,
          },
          integration: {
            type: JsonSchemaType.STRING,
          },
          token_oauth2: {
            type: JsonSchemaType.OBJECT,
            properties: {
              code: {
                type: JsonSchemaType.STRING,
              },
              redirect_uri: {
                type: JsonSchemaType.STRING,
              },
            },
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
              ingested_at: {
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
      use_authorizer: true,
    };
  };

  connectionGet = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
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
      layers: layers,
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
                ingested_at: {
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
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };

  connectionDelete = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
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
        layers: layers,
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
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };

  integrationGet = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
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
        layers: layers,
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
      use_authorizer: true,
    };
  };

  getSyncMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-sync-lambda`, {
      entry: path.join(__dirname, "assets"),
      index: "sync.py",
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
      modelName: "SyncRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          connection: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["connection"],
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "SyncResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          succees: {
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
      use_authorizer: true,
    };
  };
}
