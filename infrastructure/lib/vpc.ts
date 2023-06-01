import { CfnOutput, Stack, StackProps } from "aws-cdk-lib";
import { IVpc, SubnetType, Vpc } from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export interface VpcStackProps extends StackProps {
  readonly stageId: string;
}

export class VpcStack extends Stack {
  public readonly vpc: IVpc;

  constructor(scope: Construct, id: string, props: VpcStackProps) {
    super(scope, id, props);

    this.vpc = new Vpc(this, "vpc", {
      maxAzs: 2,
      subnetConfiguration: [
        {
          cidrMask: 24,
          name: "public",
          subnetType: SubnetType.PUBLIC,
        },
        {
          cidrMask: 24,
          name: "isolated",
          subnetType: SubnetType.PRIVATE_ISOLATED,
        },
        {
          cidrMask: 24,
          name: "private",
          subnetType: SubnetType.PRIVATE_WITH_EGRESS,
        },
      ],
      natGateways: 0,
    });

    new CfnOutput(this, "vpcId", {
      value: this.vpc.vpcId,
      exportName: "vpcId",
    });
  }
}
