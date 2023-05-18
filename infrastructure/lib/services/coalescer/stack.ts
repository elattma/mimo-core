import { Stack, StackProps } from "aws-cdk-lib";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";
import { BatchStack } from "./batch";
import { S3Stack } from "./s3";

export interface CoalescerStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
}

export class CoalescerStack extends Stack {
  constructor(scope: Construct, id: string, props: CoalescerStackProps) {
    super(scope, id, props);

    const s3 = new S3Stack(this, "S3Stack", {
      stageId: props.stageId,
      vpc: props.vpc,
    });

    const batch = new BatchStack(this, "BatchStack", {
      vpc: props.vpc,
      stageId: props.stageId,
      dataLake: s3.dataLake,
    });
  }
}
