import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import { Size, Stack, StackProps } from "aws-cdk-lib";
import { RestApi } from "aws-cdk-lib/aws-apigateway";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { ContainerImage, LogDriver } from "aws-cdk-lib/aws-ecs";
import {
  Effect,
  ManagedPolicy,
  PolicyStatement,
  Role,
  ServicePrincipal,
} from "aws-cdk-lib/aws-iam";
import { IFunction } from "aws-cdk-lib/aws-lambda";
import { LogGroup, RetentionDays } from "aws-cdk-lib/aws-logs";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
} from "aws-cdk-lib/aws-s3";
import {
  Choice,
  Condition,
  IChainable,
  Map,
  StateMachine,
  TaskInput,
  TaskStateBase,
} from "aws-cdk-lib/aws-stepfunctions";
import {
  BatchSubmitJob,
  CallApiGatewayRestApiEndpoint,
  HttpMethod,
  LambdaInvoke,
} from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";
import path = require("path");

export interface CoalescerStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly paramsFunction: IFunction;
  readonly indexFunction: IFunction;
  readonly api: RestApi;
}

export class CoalescerStack extends Stack {
  constructor(scope: Construct, id: string, props: CoalescerStackProps) {
    super(scope, id, props);
    const dataLakeS3 = this.getLake(props.stageId);

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
    const tundra = this.getJob("tundra", Size.gibibytes(8), 2, {
      STAGE: props.stageId,
      DATA_LAKE: dataLakeS3.bucketName,
    });
    if (!tundra.container.jobRole) throw new Error("Job role not found");
    dataLakeS3.grantReadWrite(tundra.container.jobRole);
    const telescope = this.getJob("telescope", Size.gibibytes(8), 2, {
      STAGE: props.stageId,
      DATA_LAKE: dataLakeS3.bucketName,
    });

    if (!telescope.container.jobRole) throw new Error("Job role not found");
    dataLakeS3.grantReadWrite(telescope.container.jobRole);

    const params = this.getParamsChainable(props.paramsFunction);
    const airbyteChainable = this.getAirbyteChainable(props.api);
    const indexChainable = this.getIndexChainable(props.indexFunction);

    const stateMachine = this.getIngestMachine(
      props.stageId,
      params,
      tundra.jobDefinitionArn,
      telescope.jobDefinitionArn,
      queue.jobQueueArn,
      airbyteChainable,
      indexChainable
    );
    stateMachine.addToRolePolicy(
      new PolicyStatement({
        actions: ["execute-api:Invoke"],
        effect: Effect.ALLOW,
        resources: ["*"],
      })
    );
  }

  getLake = (stageId: string) => {
    return new Bucket(this, "data-lake", {
      bucketName: `mimo-${stageId}-data-lake`,
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });
  };

  getJob = (
    name: string,
    memory: Size,
    cpu: number,
    environment: { [key: string]: string }
  ): EcsJobDefinition => {
    const containerDefinition = new EcsFargateContainerDefinition(
      this,
      `${name}-container`,
      {
        image: ContainerImage.fromAsset(path.join(__dirname, `${name}`)),
        memory: memory,
        cpu: cpu,
        environment: environment,
        logging: LogDriver.awsLogs({
          streamPrefix: `batch-${name}-logs`,
        }),
        assignPublicIp: true,
        command: [
          "python",
          "app.py",
          "--user",
          "Ref::user",
          "--connection",
          "Ref::connection",
          "--integration",
          "Ref::integration",
          "--access_token",
          "Ref::access_token",
        ],
        jobRole: new Role(this, `${name}-role`, {
          assumedBy: new ServicePrincipal("ecs-tasks.amazonaws.com"),
          managedPolicies: [
            ManagedPolicy.fromAwsManagedPolicyName(
              "service-role/AmazonECSTaskExecutionRolePolicy"
            ),
          ],
        }),
      }
    );
    return new EcsJobDefinition(this, `${name}-job`, {
      container: containerDefinition,
    });
  };

  getIngestMachine = (
    stage: string,
    paramsChainable: TaskStateBase,
    ingestJobArn: string,
    telescopeJobArn: string,
    jobQueueArn: string,
    airbyteChainable: IChainable,
    indexChainable: IChainable
  ): StateMachine => {
    const ingestJob = new BatchSubmitJob(this, "mimo-ingest-job", {
      jobDefinitionArn: ingestJobArn,
      jobName: `mimo-${stage}-ingest-job`,
      jobQueueArn: jobQueueArn,
      payload: TaskInput.fromJsonPathAt("$.params.Payload.params"),
      resultPath: "$.ingest",
    });

    const telescopeJob = new BatchSubmitJob(this, "mimo-telescope-job", {
      jobDefinitionArn: telescopeJobArn,
      jobName: `mimo-${stage}-telescope-job`,
      jobQueueArn: jobQueueArn,
      payload: TaskInput.fromJsonPathAt("$.params.Payload.params"),
      resultPath: "$.telescope",
    });

    return new StateMachine(this, "mimo-ingest", {
      definition: paramsChainable
        .next(
          new Choice(this, "Airbyte or Batch?")
            .when(
              Condition.stringEquals(
                "$.params.Payload.params.airbyte_id",
                "batch"
              ),
              ingestJob
            )
            .otherwise(airbyteChainable)
        )
        .toSingleState("Ingested")
        .next(telescopeJob)
        .next(indexChainable),
      logs: {
        destination: new LogGroup(this, "mimo-ingest-logs", {
          logGroupName: `mimo-${stage}-ingest-logs`,
          retention: RetentionDays.ONE_WEEK,
        }),
      },
    });
  };

  getAirbyteChainable = (api: RestApi): IChainable => {
    const ingestJob = new CallApiGatewayRestApiEndpoint(this, "ingest-job", {
      api: api,
      method: HttpMethod.POST,
      apiPath: "/airbyte/api/v1/connections/sync",
      requestBody: TaskInput.fromJsonPathAt("$.params.connection"),
      stageName: api.deploymentStage.stageName,
    });
    return ingestJob;
    // const listWorkspaces = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "list-workspaces",
    //   {
    //     api: api,
    //     apiPath: "/airbyte/api/v1/workspaces/list",
    //     stageName: api.deploymentStage.stageName,
    //     method: HttpMethod.POST,
    //     resultSelector: {
    //       workspaceId: "$.workspaces[0].workspaceId",
    //     },
    //     resultPath: "$.airbyte",
    //   }
    // );

    // const createSource = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "create-source",
    //   {
    //     api: api,
    //     apiPath: "/airbyte/api/v1/sources/create",
    //     requestBody: TaskInput.fromObject({
    //       workspaceId: JsonPath.stringAt("$.airbyte.workspaceId"),
    //       name: JsonPath.stringAt("$.params.connection"),
    //       sourceDefinitionId: JsonPath.stringAt("$.params.airbyte_id"),
    //     }),
    //     stageName: api.deploymentStage.stageName,
    //     method: HttpMethod.POST,
    //   }
    // );

    // const createDestination = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "create-destination",
    //   {
    //     api: api,
    //     method: HttpMethod.POST,
    //     apiPath: "/airbyte/api/v1/destinations/create",
    //     requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //     stageName: api.deploymentStage.stageName,
    //   }
    // );

    // const createConnection = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "create-connection",
    //   {
    //     api: api,
    //     method: HttpMethod.POST,
    //     apiPath: "/airbyte/api/v1/connections/create",
    //     requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //     stageName: api.deploymentStage.stageName,
    //   }
    // );

    // const ingestJob = new CallApiGatewayRestApiEndpoint(this, "ingest-job", {
    //   api: api,
    //   method: HttpMethod.POST,
    //   apiPath: "/airbyte/api/v1/connections/sync",
    //   requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //   stageName: api.deploymentStage.stageName,
    // });

    // const deleteConnection = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "delete-connection",
    //   {
    //     api: api,
    //     method: HttpMethod.POST,
    //     apiPath: "/airbyte/api/v1/connections/delete",
    //     requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //     stageName: api.deploymentStage.stageName,
    //   }
    // );

    // const deleteDestination = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "delete-destination",
    //   {
    //     api: api,
    //     method: HttpMethod.POST,
    //     apiPath: "/airbyte/api/v1/destinations/delete",
    //     requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //     stageName: api.deploymentStage.stageName,
    //   }
    // );

    // const deleteSource = new CallApiGatewayRestApiEndpoint(
    //   this,
    //   "delete-source",
    //   {
    //     api: api,
    //     method: HttpMethod.POST,
    //     apiPath: "/airbyte/api/v1/sources/delete",
    //     requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    //     stageName: api.deploymentStage.stageName,
    //   }
    // );

    // return new Parallel(this, "Create Source, Destination")
    //   .branch(createSource)
    //   .branch(createDestination)
    //   .next(createConnection)
    //   .next(ingestJob)
    //   .next(deleteConnection)
    //   .next(
    //     new Parallel(this, "Delete Source, Destination")
    //       .branch(deleteDestination)
    //       .branch(deleteSource)
    //   );
  };

  getIndexChainable = (indexFunction: IFunction): IChainable => {
    const indexJob = new LambdaInvoke(this, "mimo-index-job", {
      lambdaFunction: indexFunction,
      payload: TaskInput.fromJsonPathAt("$.params.Payload.params"),
      resultPath: "$.index",
    });

    return new Map(this, "Index Data", {
      maxConcurrency: 5,
    }).iterator(indexJob);
  };

  getParamsChainable = (paramsFunction: IFunction): TaskStateBase => {
    return new LambdaInvoke(this, "mimo-params-job", {
      lambdaFunction: paramsFunction,
      payload: TaskInput.fromJsonPathAt("$.input"),
      resultSelector: {
        params: "$.Payload.params",
      },
    });
  };
}
