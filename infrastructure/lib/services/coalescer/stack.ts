import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import { Size, Stack, StackProps } from "aws-cdk-lib";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { ContainerImage, LogDriver } from "aws-cdk-lib/aws-ecs";
import { Cluster, ICluster } from "aws-cdk-lib/aws-eks";
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
  Parallel,
  StateMachine,
  TaskInput,
  TaskStateBase,
} from "aws-cdk-lib/aws-stepfunctions";
import {
  BatchSubmitJob,
  EksCall,
  HttpMethods,
  LambdaInvoke,
} from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";
import path = require("path");

export interface CoalescerStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly paramsFunction: IFunction;
  readonly indexFunction: IFunction;
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
    const telescope = this.getJob("telescope", Size.gibibytes(8), 2, {
      STAGE: props.stageId,
      DATA_LAKE: dataLakeS3.bucketName,
    });

    const clusterName = process.env.CLUSTER_NAME || "";
    const clusterEndpoint = process.env.CLUSTER_ENDPOINT;
    const clusterCertificateAuthorityData = process.env.CLUSTER_CAD;
    const airbyteCluster = Cluster.fromClusterAttributes(
      this,
      "airbyte-cluster",
      {
        clusterName: clusterName,
        clusterEndpoint: clusterEndpoint,
        clusterCertificateAuthorityData: clusterCertificateAuthorityData,
      }
    );

    const params = this.getParamsChainable(props.paramsFunction);
    const airbyteChainable = this.getAirbyteChainable(airbyteCluster);
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

  getAirbyteChainable = (airbyte: ICluster): IChainable => {
    const createSource = new EksCall(this, "airbyte-create-source", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/sources/create",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const createDestination = new EksCall(this, "airbyte-create-destination", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/destinations/create",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const createConnection = new EksCall(this, "airbyte-create-connection", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/connections/create",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const ingestJob = new EksCall(this, "airbyte-ingest-job", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/connections/sync",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const deleteConnection = new EksCall(this, "airbyte-delete-connection", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/connections/delete",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const deleteDestination = new EksCall(this, "airbyte-delete-destination", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/destinations/delete",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    const deleteSource = new EksCall(this, "airbyte-delete-source", {
      cluster: airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/sources/delete",
      requestBody: TaskInput.fromJsonPathAt("$.params.Payload.params"),
    });

    return new Parallel(this, "Create Source, Destination")
      .branch(createSource)
      .branch(createDestination)
      .next(createConnection)
      .next(ingestJob)
      .next(deleteConnection)
      .next(
        new Parallel(this, "Delete Source, Destination")
          .branch(deleteDestination)
          .branch(deleteSource)
      );
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
      resultPath: "$.params",
    });
  };
}
