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
import {
  IRestApi,
  JsonSchemaType,
  ModelOptions,
} from "aws-cdk-lib/aws-apigateway";
import { ITable } from "aws-cdk-lib/aws-dynamodb";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { ContainerImage, LogDriver } from "aws-cdk-lib/aws-ecs";
import {
  ManagedPolicy,
  PolicyStatement,
  Role,
  ServicePrincipal,
} from "aws-cdk-lib/aws-iam";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { LogGroup } from "aws-cdk-lib/aws-logs";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
  IBucket,
} from "aws-cdk-lib/aws-s3";
import {
  Choice,
  Condition,
  Fail,
  IChainable,
  JsonPath,
  Pass,
  Result,
  StateMachine,
  Succeed,
  TaskInput,
  Wait,
  WaitTime,
} from "aws-cdk-lib/aws-stepfunctions";
import {
  BatchSubmitJob,
  CallApiGatewayRestApiEndpoint,
  CallAwsService,
  DynamoAttributeValue,
  DynamoGetItem,
  DynamoUpdateItem,
  HttpMethod,
} from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface ConnectorStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly mimoTable: ITable;
  readonly airbyteApi: IRestApi;
  readonly uploadBucket: IBucket;
}

export class ConnectorStack extends Stack {
  readonly methods: MethodConfig[] = [];
  readonly integrationMethods: MethodConfig[] = [];
  readonly libraryMethods: MethodConfig[] = [];
  readonly layers: PythonLayerVersion[] = [];
  readonly definition: EcsJobDefinition;
  readonly syncMethod: MethodConfig;
  readonly uploadMethod: MethodConfig;

  constructor(scope: Construct, id: string, props: ConnectorStackProps) {
    super(scope, id, props);
    const batch = new FargateComputeEnvironment(this, "coalesce-batch", {
      vpc: props.vpc,
      spot: true,
      vpcSubnets: {
        subnets: props.vpc.publicSubnets,
      },
    });

    const queue = new JobQueue(this, "coalesce-queue", {
      priority: 1,
    });
    queue.addComputeEnvironment(batch, 1);
    this.definition = this.getDefinition(props.stageId);
    if (!this.definition.container.jobRole) {
      throw new Error("Job role is required");
    }
    this.definition.container.jobRole.addToPrincipalPolicy(
      new PolicyStatement({
        actions: [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:ListTables",
          "dynamodb:DescribeTable",
          "dynamodb:Query",
        ],
        resources: ["*"],
      })
    );
    this.definition.container.jobRole.addToPrincipalPolicy(
      new PolicyStatement({
        actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
        resources: ["*"],
      })
    );

    const util = new PythonLayerVersion(this, `${props.stageId}-util-layer`, {
      entry: path.join(__dirname, `layers/util`),
      bundling: {
        assetExcludes: ["**.venv**", "**pycache**"],
      },
      compatibleRuntimes: [Runtime.PYTHON_3_9],
    });
    this.layers.push(util);
    const createMethod = this.connectionPost(props.stageId, props.airbyteApi);
    this.methods.push(createMethod);
    const getMethod = this.connectionGet(props.stageId);
    this.methods.push(getMethod);
    const deleteMethod = this.connectionDelete(props.stageId, props.airbyteApi);
    this.methods.push(deleteMethod);

    const integrationsMethod = this.integrationGet(props.stageId);
    this.integrationMethods.push(integrationsMethod);

    const libraryMethod = this.libraryGet(props.stageId);
    this.libraryMethods.push(libraryMethod);

    const syncSfn = this.getSyncSfn(
      props.stageId,
      props.mimoTable,
      props.airbyteApi,
      this.definition,
      queue
    );
    this.syncMethod = this.sync(props.stageId, syncSfn);
    this.uploadMethod = this.connectionUpload(
      props.stageId,
      props.uploadBucket
    );
  }

  sync = (stage: string, syncSfn: StateMachine): MethodConfig => {
    const handler = new PythonFunction(this, "sync-lambda", {
      entry: path.join(__dirname, "connection"),
      index: "sync.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        SFN_ARN: syncSfn.stateMachineArn,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: this.layers,
    });
    syncSfn.grantStartExecution(handler);

    const methodRequestOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "SyncRequest",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          connection: {
            type: JsonSchemaType.STRING,
          },
          library: {
            type: JsonSchemaType.STRING,
          },
        },
      },
    };

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "SyncResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
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

  getUpdateStatus = (
    table: ITable,
    name: string,
    status: "IN_PROGRESS" | "SUCCESS" | "FAILED" | string
  ): IChainable => {
    return new DynamoUpdateItem(this, `${name}-${status}`, {
      table: table,
      key: {
        parent: DynamoAttributeValue.fromString(
          JsonPath.format("LIBRARY#{}", JsonPath.stringAt("$.input.library"))
        ),
        child: DynamoAttributeValue.fromString(
          JsonPath.format(
            "CONNECTION#{}",
            JsonPath.stringAt("$.input.connection")
          )
        ),
      },
      updateExpression: "SET #sync = :sync",
      expressionAttributeNames: {
        "#sync": "sync",
      },
      expressionAttributeValues: {
        ":sync": DynamoAttributeValue.fromMap({
          status: DynamoAttributeValue.fromString(status),
          checkpoint_at: DynamoAttributeValue.fromNumber(
            JsonPath.numberAt("$.timestamp")
          ),
          ingested_at: DynamoAttributeValue.fromNumber(
            status === "SUCCESS"
              ? JsonPath.numberAt("$.timestamp")
              : JsonPath.numberAt(
                  "$.libraryConnectionItem.Item.sync.M.ingested_at.N"
                )
          ),
        }),
      },
      resultPath: "$.updateResult",
    });
  };

  getSyncSfn = (
    stage: string,
    table: ITable,
    api: IRestApi,
    jobDefinition: EcsJobDefinition,
    queue: JobQueue
  ): StateMachine => {
    return new StateMachine(this, `${stage}-sync`, {
      definition: new DynamoGetItem(this, "Get Connection State", {
        table: table,
        key: {
          parent: DynamoAttributeValue.fromString(
            JsonPath.format("LIBRARY#{}", JsonPath.stringAt("$.input.library"))
          ),
          child: DynamoAttributeValue.fromString(
            JsonPath.format(
              "CONNECTION#{}",
              JsonPath.stringAt("$.input.connection")
            )
          ),
        },
        resultPath: "$.libraryConnectionItem",
        consistentRead: true,
      })
        .next(
          new Choice(this, "Is Lock Held")
            .when(
              Condition.isNotPresent("$.libraryConnectionItem.Item"),
              new Fail(this, "Connection not found")
            )
            .when(
              Condition.stringEquals(
                "$.libraryConnectionItem.Item.sync.M.status.S",
                "IN_PROGRESS"
              ),
              new Succeed(this, "Already running")
            )
            .otherwise(this.getUpdateStatus(table, "Hold Lock", "IN_PROGRESS"))
        )
        .toSingleState("Single State lock", {
          outputPath: "$[0]",
        })
        .next(
          new CallAwsService(this, "Find if Airbyte-Managed", {
            service: "ssm",
            action: "getParameter",
            parameters: {
              Name: JsonPath.format(
                `/${stage}/integrations/{}/airbyte_id`,
                JsonPath.stringAt("$.libraryConnectionItem.Item.integration.S")
              ),
            },
            resultSelector: {
              airbyte_id: JsonPath.stringAt("$.Parameter.Value"),
            },
            resultPath: "$.params",
            iamResources: ["*"],
          })
        )
        .next(
          new Choice(this, "Airbyte or Batch?")
            .when(
              Condition.stringEquals("$.params.airbyte_id", "batch"),
              new BatchSubmitJob(this, "Submit Batch Job", {
                jobDefinitionArn: jobDefinition.jobDefinitionArn,
                jobQueueArn: queue.jobQueueArn,
                jobName: `${stage}-sync`,
                payload: TaskInput.fromObject({
                  library: JsonPath.stringAt("$.input.library"),
                  connection: JsonPath.stringAt("$.input.connection"),
                }),
                resultPath: "$.batchResult",
                resultSelector: {
                  "exitCode.$": "$.Container.ExitCode",
                },
              }).next(
                new Choice(this, "Batch Job Completed")
                  .when(
                    Condition.numberEquals("$.batchResult.exitCode", 200),
                    new Pass(this, "Batch Job Succeeded", {
                      result: Result.fromString("SUCCESS"),
                      resultPath: "$.ingestionStatus",
                    })
                  )
                  .otherwise(
                    new Pass(this, "Batch Job Failed", {
                      result: Result.fromString("FAILED"),
                      resultPath: "$.ingestionStatus",
                    })
                  )
              )
            )
            .otherwise(
              new CallApiGatewayRestApiEndpoint(this, "Manual Airbyte Sync", {
                api: api,
                stageName: "prod",
                method: HttpMethod.POST,
                apiPath: "/airbyte/api/v1/connections/sync",
                requestBody: TaskInput.fromObject({
                  connectionId: JsonPath.stringAt("$.input.connection"),
                }),
                resultPath: "$.airbyteResult",
              }).next(this.getWaitForAirbyte(api))
            )
        )
        .toSingleState("Single State Ingest", {
          outputPath: "$[0]",
        })
        .next(
          new Choice(this, "Update Status")
            .when(
              Condition.stringEquals("$.ingestionStatus", "SUCCESS"),
              this.getUpdateStatus(table, "Release Lock", "SUCCESS")
            )
            .otherwise(this.getUpdateStatus(table, "Release Lock", "FAILED"))
        ),
      logs: {
        destination: new LogGroup(this, `${stage}-sync-logs`),
      },
    });
  };

  getWaitForAirbyte = (api: IRestApi): IChainable => {
    const checkAirbyte = new Wait(this, "Wait for Airbyte", {
      time: WaitTime.duration(Duration.minutes(2)),
    }).next(
      new CallApiGatewayRestApiEndpoint(this, "Check Airbyte Job status", {
        api: api,
        stageName: "prod",
        method: HttpMethod.POST,
        apiPath: "/airbyte/api/v1/jobs/get_last_replication_job",
        requestBody: TaskInput.fromObject({
          connectionId: JsonPath.stringAt("$.input.connection"),
        }),
        resultPath: "$.checkAirbyteResult",
      })
    );

    return checkAirbyte.next(
      new Choice(this, "Airbyte Job Exists?").when(
        Condition.isNotNull("$.checkAirbyteResult.ResponseBody.job"),
        new Choice(this, "Airbyte Job Complete?")
          .when(
            Condition.or(
              Condition.stringEquals(
                "$.checkAirbyteResult.ResponseBody.job.status",
                "pending"
              ),
              Condition.stringEquals(
                "$.checkAirbyteResult.ResponseBody.job.status",
                "running"
              )
            ),
            checkAirbyte
          )
          .when(
            Condition.stringEquals(
              "$.checkAirbyteResult.ResponseBody.job.status",
              "succeeded"
            ),
            new Pass(this, "Airbyte Job Succeeded", {
              result: Result.fromString("SUCCESS"),
              resultPath: "$.ingestionStatus",
            })
          )
          .otherwise(
            new Pass(this, "Airbyte Job Failed", {
              result: Result.fromString("FAILED"),
              resultPath: "$.ingestionStatus",
            })
          )
      )
    );
  };

  getDefinition = (stage: string): EcsJobDefinition => {
    const container = new EcsFargateContainerDefinition(
      this,
      "coalescer-container",
      {
        image: ContainerImage.fromAsset(path.join(__dirname)),
        memory: Size.gibibytes(4),
        cpu: 2,
        environment: {
          PARENT_CHILD_TABLE: `mimo-${stage}-pc`,
          INTEGRATIONS_PATH: `/${stage}/integrations`,
          APP_SECRETS_PATH: `/${stage}/app_secrets`,
        },
        logging: LogDriver.awsLogs({
          streamPrefix: `batch-coalescer-logs`,
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
        jobRole: new Role(this, `coalescer-role`, {
          assumedBy: new ServicePrincipal("ecs-tasks.amazonaws.com"),
          managedPolicies: [
            ManagedPolicy.fromAwsManagedPolicyName(
              "service-role/AmazonECSTaskExecutionRolePolicy"
            ),
          ],
        }),
      }
    );
    return new EcsJobDefinition(this, `coalescer-job`, {
      container: container,
    });
  };

  getLake = (stageId: string) => {
    return new Bucket(this, "data-lake", {
      bucketName: `mimo-${stageId}-data-lake`,
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });
  };

  connectionUpload = (stage: string, uploadBucket: IBucket): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-connector-upload-lambda`,
      {
        entry: path.join(__dirname, "connection"),
        index: "upload.py",
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        timeout: Duration.seconds(30),
        memorySize: 1024,
        environment: {
          STAGE: stage,
          UPLOAD_BUCKET: uploadBucket.bucketName,
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
      modelName: "UploadResponse",
      schema: {
        title: "UploadResponse",
        type: JsonSchemaType.OBJECT,
        properties: {
          signed_url: {
            type: JsonSchemaType.STRING,
          },
        },
        required: ["signed_url"],
      },
    };

    return {
      name: "GET",
      handler: handler,
      requestParameters: {
        "method.request.querystring.library": true,
      },
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
  };

  connectionPost = (stage: string, airbyteApi: IRestApi): MethodConfig => {
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
          AIRBYTE_ENDPOINT: `https://${airbyteApi.restApiId}.execute-api.${this.region}.amazonaws.com/prod/airbyte/api`,
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
          config: {
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
          library: {
            type: JsonSchemaType.STRING,
          },
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
        required: ["library", "connections"],
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

  connectionDelete = (stage: string, airbyteApi: IRestApi): MethodConfig => {
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
          AIRBYTE_ENDPOINT: `https://${airbyteApi.restApiId}.execute-api.${this.region}.amazonaws.com/prod/airbyte/api`,
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
