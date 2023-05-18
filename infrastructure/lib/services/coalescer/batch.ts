import {
  EcsFargateContainerDefinition,
  EcsJobDefinition,
  FargateComputeEnvironment,
  JobQueue,
} from "@aws-cdk/aws-batch-alpha";
import { NestedStack, Size, StackProps } from "aws-cdk-lib";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { ContainerImage } from "aws-cdk-lib/aws-ecs";
import { IBucket } from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";
import path = require("path");

export interface BatchStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly dataLake: IBucket;
}

export class BatchStack extends NestedStack {
  readonly jobsMap: { [key: string]: EcsJobDefinition } = {};

  constructor(scope: Construct, id: string, props: BatchStackProps) {
    super(scope, id, props);

    const batch = new FargateComputeEnvironment(this, "coalesce-batch", {
      vpc: props.vpc,
      spot: true,
    });

    const queue = new JobQueue(this, "coalesce-queue", {
      priority: 1,
    });
    queue.addComputeEnvironment(batch, 1);

    const tundraName = "tundra";
    this.jobsMap[tundraName] = this.defineJob({
      name: tundraName,
      memory: Size.mebibytes(8192),
      cpu: 4096,
      environment: {
        STAGE: props.stageId,
        DATA_LAKE: props.dataLake.bucketName,
      },
    });

    // const icebergName = "iceberg";
    // this.jobsMap[icebergName] = this.defineJob({
    //   name: icebergName,
    //   memory: Size.mebibytes(8192),
    //   cpu: 4096,
    //   environment: {
    //     STAGE: props.stageId,
    //     DATA_LAKE: props.dataLake.bucketName,
    //   },
    // });

    // const telescopeName = "telescope";
    // this.jobsMap[telescopeName] = this.defineJob({
    //   name: telescopeName,
    //   memory: Size.mebibytes(8192),
    //   cpu: 4096,
    //   environment: {
    //     STAGE: props.stageId,
    //     DATA_LAKE: props.dataLake.bucketName,
    //   },
    // });
  }

  defineJob = (jobProps: JobProps): EcsJobDefinition => {
    const containerDefinition = new EcsFargateContainerDefinition(
      this,
      `${jobProps.name}-container`,
      {
        image: ContainerImage.fromAsset(
          path.join(__dirname, `${jobProps.name}`)
        ),
        memory: jobProps.memory,
        cpu: jobProps.cpu,
        environment: jobProps.environment,
        command: ["python", `${jobProps.name}.py`],
      }
    );
    const jobDefinition = new EcsJobDefinition(this, `${jobProps.name}-job`, {
      container: containerDefinition,
    });
    return jobDefinition;
  };
}

interface JobProps {
  readonly name: string;
  readonly memory: Size;
  readonly cpu: number;
  readonly environment: { [key: string]: string };
}
