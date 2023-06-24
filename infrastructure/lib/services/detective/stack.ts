import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Size, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { ContainerImage, LogDriver } from "aws-cdk-lib/aws-ecs";
import {
  ManagedPolicy,
  PolicyStatement,
  Role,
  ServicePrincipal,
} from "aws-cdk-lib/aws-iam";
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
  readonly graphPlotDefinition: EcsJobDefinition;
  readonly graphPlotQueue: JobQueue;

  constructor(scope: Construct, id: string, props: DetectiveStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
    const contextMethod = this.contextMethod(props.stageId, layers);
    this.methods.push(contextMethod);
    this.v0GetContextMethod = this.getV0GetContextMethod(props.stageId, layers);

    const batch = new FargateComputeEnvironment(this, "graph_plot-batch", {
      vpc: props.vpc,
      spot: true,
      vpcSubnets: {
        subnets: props.vpc.publicSubnets,
      },
    });
    this.graphPlotQueue = new JobQueue(this, "graph_plot-queue", {
      priority: 1,
    });
    this.graphPlotQueue.addComputeEnvironment(batch, 1);
    this.graphPlotDefinition = this.getDefinition(props.stageId);
    if (!this.graphPlotDefinition.container.jobRole) {
      throw new Error("Job role is required");
    }
    this.graphPlotDefinition.container.jobRole.addToPrincipalPolicy(
      new PolicyStatement({
        actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
        resources: ["*"],
      })
    );
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
        index: "context.py",
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

  getDefinition = (stage: string): EcsJobDefinition => {
    const container = new EcsFargateContainerDefinition(
      this,
      "graph_plot-container",
      {
        image: ContainerImage.fromAsset(path.join(__dirname)),
        memory: Size.gibibytes(4),
        cpu: 2,
        environment: {
          LAKE_BUCKET_NAME: `mimo-${stage}-lake`,
          APP_SECRETS_PATH: `/${stage}/app_secrets`,
          NEO4J_URI: "neo4j+s://67eff9a1.databases.neo4j.io",
        },
        logging: LogDriver.awsLogs({
          streamPrefix: `batch-graph_plot-logs`,
        }),
        assignPublicIp: true,
        command: [
          "python",
          "app.py",
          "--connection",
          "Ref::connection",
          "--library",
          "Ref::library",
        ],
        jobRole: new Role(this, `graph_plot-role`, {
          assumedBy: new ServicePrincipal("ecs-tasks.amazonaws.com"),
          managedPolicies: [
            ManagedPolicy.fromAwsManagedPolicyName(
              "service-role/AmazonECSTaskExecutionRolePolicy"
            ),
          ],
        }),
      }
    );
    return new EcsJobDefinition(this, `graph_plot-job`, {
      container: container,
    });
  };
}
