import { NestedStack, StackProps } from "aws-cdk-lib";
import {
  GatewayVpcEndpointAwsService,
  IVpc,
  SubnetType,
} from "aws-cdk-lib/aws-ec2";
import {
  BlockPublicAccess,
  Bucket,
  BucketEncryption,
  IBucket,
} from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export interface S3StackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
}

export class S3Stack extends NestedStack {
  readonly dataLake: IBucket;

  constructor(scope: Construct, id: string, props: S3StackProps) {
    super(scope, id, props);

    this.dataLake = new Bucket(this, "data-lake", {
      bucketName: `mimo-${props.stageId}-data-lake`,
      encryption: BucketEncryption.S3_MANAGED,
      blockPublicAccess: BlockPublicAccess.BLOCK_ALL,
    });

    props.vpc.addGatewayEndpoint("s3-gateway", {
      service: GatewayVpcEndpointAwsService.S3,
      subnets: [
        {
          subnetType: SubnetType.PRIVATE_ISOLATED,
        },
      ],
    });
  }
}
