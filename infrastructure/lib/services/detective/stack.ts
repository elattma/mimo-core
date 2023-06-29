import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface DetectiveStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
}

export class DetectiveStack extends Stack {
  readonly methods: MethodConfig[] = [];
  readonly indexLambda: PythonFunction;
  readonly v0GetContextMethod: MethodConfig;

  constructor(scope: Construct, id: string, props: DetectiveStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
    const util = new PythonLayerVersion(
      this,
      `${props.stageId}-detective-util-layer`,
      {
        entry: path.join(__dirname, `layers/util`),
        bundling: {
          assetExcludes: ["**.venv**", "**pycache**"],
        },
        compatibleRuntimes: [Runtime.PYTHON_3_9],
      }
    );
    layers.push(util);
    const contextMethod = this.contextMethod(props.stageId, layers);
    this.methods.push(contextMethod);
    this.v0GetContextMethod = this.getV0GetContextMethod(props.stageId, layers);
  }

  contextMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-detective-context-lambda`,
      {
        entry: path.join(__dirname, "v1"),
        index: "get.py",
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        timeout: Duration.minutes(15),
        memorySize: 1024,
        environment: {
          STAGE: stage,
          NEO4J_URI: "neo4j+s://67eff9a1.databases.neo4j.io",
          APP_SECRETS_PATH: `/${stage}/app_secrets`,
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
      modelName: "ContextRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          query: {
            type: JsonSchemaType.OBJECT,
            properties: {
              lingua: {
                type: JsonSchemaType.STRING,
              },
              integrations: {
                type: JsonSchemaType.ARRAY,
                items: {
                  type: JsonSchemaType.STRING,
                },
              },
              concepts: {
                type: JsonSchemaType.ARRAY,
                items: {
                  type: JsonSchemaType.STRING,
                },
              },
              entities: {
                type: JsonSchemaType.ARRAY,
                items: {
                  type: JsonSchemaType.STRING,
                },
              },
              time_start: {
                type: JsonSchemaType.INTEGER,
              },
              time_end: {
                type: JsonSchemaType.INTEGER,
              },
              time_sort: {
                type: JsonSchemaType.STRING,
                enum: ["asc", "desc"],
              },
              limit: {
                type: JsonSchemaType.INTEGER,
              },
              offset: {
                type: JsonSchemaType.INTEGER,
              },
              search_method: {
                type: JsonSchemaType.STRING,
                enum: ["exact", "relevant"],
              },
            },
            required: ["lingua"],
          },
          library: {
            type: JsonSchemaType.STRING,
          },
          token_limit: {
            type: JsonSchemaType.INTEGER,
          },
          next_token: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["query"],
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ContextResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          blocks: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                id: {
                  type: JsonSchemaType.STRING,
                },
                label: {
                  type: JsonSchemaType.STRING,
                },
                integration: {
                  type: JsonSchemaType.STRING,
                },
                connection: {
                  type: JsonSchemaType.STRING,
                },
                last_updated_ts: {
                  type: JsonSchemaType.INTEGER,
                },
                properties: {
                  type: JsonSchemaType.ARRAY,
                  items: {
                    type: JsonSchemaType.OBJECT,
                    properties: {
                      type: {
                        type: JsonSchemaType.STRING,
                        enum: ["structured", "unstructured"],
                      },
                      key: {
                        type: JsonSchemaType.STRING,
                      },
                      value: {
                        type: JsonSchemaType.STRING,
                      },
                      chunks: {
                        type: JsonSchemaType.ARRAY,
                        items: {
                          type: JsonSchemaType.OBJECT,
                          properties: {
                            order: {
                              type: JsonSchemaType.INTEGER,
                            },
                            text: {
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
          },
          next_token: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["blocks"],
      },
    };

    return {
      name: "POST",
      handler: handler,
      apiKeyRequired: true,
      authorizerType: AuthorizerType.API_KEY,
      requestModelOptions: methodRequestOptions,
      responseModelOptions: methodResponseOptions,
    };
  };

  getV0GetContextMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-detective-v0-context-lambda`,
      {
        entry: path.join(__dirname, "v0"),
        index: "get.py",
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        timeout: Duration.minutes(15),
        memorySize: 1024,
        environment: {
          STAGE: stage,
          GRAPH_DB_URI: "neo4j+s://67eff9a1.databases.neo4j.io",
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
      modelName: "V0ContextGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          contexts: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                text: {
                  type: JsonSchemaType.STRING,
                },
                score: {
                  type: JsonSchemaType.NUMBER,
                },
                source: {
                  type: JsonSchemaType.OBJECT,
                  properties: {
                    integration: {
                      type: JsonSchemaType.STRING,
                    },
                    page: {
                      type: JsonSchemaType.STRING,
                    },
                  },
                },
              },
            },
          },
          next_token: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["contexts"],
      },
    };

    return {
      name: "GET",
      handler: handler,
      requestParameters: {
        "method.request.querystring.query": true,
        "method.request.querystring.max_tokens": false,
        "method.request.querystring.next_token": false,
      },
      apiKeyRequired: true,
      authorizerType: AuthorizerType.API_KEY,
      responseModelOptions: methodResponseOptions,
    };
  };
}
