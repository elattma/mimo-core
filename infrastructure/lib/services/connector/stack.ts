import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
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
import { ILayerVersion, Runtime } from "aws-cdk-lib/aws-lambda";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
} from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface CoalescerStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly layers: ILayerVersion[];
}

export class CoalescerStack extends Stack {
  readonly syncPost: MethodConfig;
  readonly definition: EcsJobDefinition;

  constructor(scope: Construct, id: string, props: CoalescerStackProps) {
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
    this.syncPost = this.getMethod(
      props.stageId,
      queue.jobQueueName,
      props.layers
    );
    this.syncPost.handler.addToRolePolicy(
      new PolicyStatement({
        actions: ["batch:SubmitJob"],
        resources: ["*"],
      })
    );
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
  }

  getMethod = (
    stage: string,
    jobQueue: string,
    layers: ILayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-coalescer-sync-lambda`, {
      entry: path.join(__dirname, "sync"),
      index: "post.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
      memorySize: 1024,
      environment: {
        STAGE: stage,
        JOB_QUEUE: jobQueue,
        JOB_DEFINITION: this.definition.jobDefinitionName,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "SyncPostResponse",
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
      name: "POST",
      handler: handler,
      idResource: "sync",
      responseModelOptions: methodResponseOptions,
      authorizerType: AuthorizerType.APP_OAUTH,
    };
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
}
