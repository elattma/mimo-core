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
          oauth2_link: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["id", "name", "description", "icon", "oauth2_link"],
      }
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
        }
      }
    };

    const layers: PythonLayerVersion[] = [];
    const createMethod = this.getCreateMethod(props.stageId, layers);
    this.methods.push(createMethod);
    const getMethod = this.getGetMethod(props.stageId, layers);
    this.methods.push(getMethod);
    const deleteMethod = this.getDeleteMethod(props.stageId, layers);
    this.methods.push(deleteMethod);

    const integrationsMethod = this.getIntegrationsMethod(
      props.stageId,
      layers
    );
    this.integrationMethods.push(integrationsMethod);
  }

  getCreateMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-create-lambda`,
      {
        entry: path.join(__dirname, "assets"),
        index: "create.py",
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
          }
        },
      },
    };

    return {
      name: "POST",
      handler: handler,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: {schema: {type: JsonSchemaType.OBJECT}},
      use_authorizer: true,
    };
  };

  getGetMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-connector-get-lambda`, {
      entry: path.join(__dirname, "assets"),
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
        required: ["id", "name", "integration", "created_at"],
      },
    };

    return {
      name: "GET",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };

  getDeleteMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-delete-lambda`,
      {
        entry: path.join(__dirname, "assets"),
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

  getIntegrationsMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-integrations-lambda`,
      {
        entry: path.join(__dirname, "assets"),
        index: "integrations.py",
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
}
