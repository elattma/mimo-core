import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import { KubectlV26Layer } from "@aws-cdk/lambda-layer-kubectl-v26";
import { Size, Stack, StackProps } from "aws-cdk-lib";
import {
  GatewayVpcEndpointAwsService,
  IVpc,
  InstanceType,
  SubnetType,
} from "aws-cdk-lib/aws-ec2";
import { ContainerImage, LogDriver } from "aws-cdk-lib/aws-ecs";
import { CapacityType, Cluster, KubernetesVersion } from "aws-cdk-lib/aws-eks";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
} from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import path = require("path");

export interface CoalescerStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
}

export class CoalescerStack extends Stack {
  constructor(scope: Construct, id: string, props: CoalescerStackProps) {
    super(scope, id, props);
    const dataLakeS3 = this.getLake(props.stageId, props.vpc);
    const airbyteCluster = this.getAirbyte(props.stageId, props.vpc);

    const batch = new FargateComputeEnvironment(this, "coalesce-batch", {
      vpc: props.vpc,
      spot: true,
    });

    const queue = new JobQueue(this, "coalesce-queue", {
      priority: 1,
    });
    queue.addComputeEnvironment(batch, 1);
    const tundra = this.getJob("tundra", Size.gibibytes(8), 2, {
      STAGE: props.stageId,
      DATA_LAKE: dataLakeS3.bucketName,
    });
  }

  getLake = (stageId: string, vpc: IVpc) => {
    const dataLake = new Bucket(this, "data-lake", {
      bucketName: `mimo-${stageId}-data-lake`,
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });

    vpc.addGatewayEndpoint("s3-gateway", {
      service: GatewayVpcEndpointAwsService.S3,
      subnets: [
        {
          subnetType: SubnetType.PRIVATE_ISOLATED,
        },
        {
          subnetType: SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
    });

    return dataLake;
  };

  getAirbyte = (stageId: string, vpc: IVpc): Cluster => {
    const kubeCtlLayer = new KubectlV26Layer(this, "kubectl-layer");

    const cluster = new Cluster(this, "eks-cluster", {
      vpc: vpc,
      version: KubernetesVersion.V1_26,
      kubectlLayer: kubeCtlLayer,
      defaultCapacity: 0,
    });

    cluster.addNodegroupCapacity("t2-ng-spot", {
      instanceTypes: [
        new InstanceType("t2.medium"),
        new InstanceType("t2.large"),
      ],
      minSize: 1,
      capacityType: CapacityType.SPOT,
    });

    cluster.addNodegroupCapacity("t3-ng-spot", {
      instanceTypes: [
        new InstanceType("t3.medium"),
        new InstanceType("t3.large"),
      ],
      minSize: 1,
      capacityType: CapacityType.SPOT,
    });

    // new HelmChart(this, "helm-airbyte", {
    //   cluster: cluster,
    //   chart: "airbyte",
    //   release: "airbyte",
    //   repository: "https://airbytehq.github.io/helm-charts",
    //   namespace: "airbyte",
    //   timeout: Duration.minutes(15),
    // });

    return cluster;
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
      }
    );
    return new EcsJobDefinition(this, `${name}-job`, {
      container: containerDefinition,
      parameters: {
        user: "default",
        connection: "default",
        integration: "default",
        access_token: "default",
        last_ingested_at: "default",
      },
    });
  };
}
