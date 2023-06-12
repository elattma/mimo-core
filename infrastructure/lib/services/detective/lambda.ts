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

export interface DetectiveStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class DetectiveStack extends Stack {
  readonly methods: MethodConfig[] = [];
  readonly indexLambda: PythonFunction;
  readonly v0GetContextMethod: MethodConfig;

  constructor(scope: Construct, id: string, props: DetectiveStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
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
        entry: path.join(__dirname, "context"),
        index: "post.py",
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

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "ContextRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          query: {
            type: JsonSchemaType.STRING,
          },
          max_tokens: {
            type: JsonSchemaType.NUMBER,
          },
          library: {
            type: JsonSchemaType.STRING,
          },
          next_token: {
            type: JsonSchemaType.STRING,
          },
          overrides: {
            type: JsonSchemaType.OBJECT,
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
          contexts: {
            type: JsonSchemaType.ARRAY,
            items: {
              type: JsonSchemaType.OBJECT,
              properties: {
                blocks: {
                  type: JsonSchemaType.ARRAY,
                  items: {
                    type: JsonSchemaType.OBJECT,
                  },
                },
                score: {
                  type: JsonSchemaType.NUMBER,
                },
                source: {
                  type: JsonSchemaType.OBJECT,
                  properties: {
                    connection: {
                      type: JsonSchemaType.STRING,
                    },
                    id: {
                      type: JsonSchemaType.STRING,
                    },
                  },
                  required: ["connection", "id"],
                },
              },
              required: ["blocks", "score", "source"],
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
