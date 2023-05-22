import { NestedStack, StackProps } from "aws-cdk-lib";
import { IVpc } from "aws-cdk-lib/aws-ec2";
import { Cluster } from "aws-cdk-lib/aws-eks";
import { IBucket } from "aws-cdk-lib/aws-s3";
import {
  BatchSubmitJob,
  EksCall,
  HttpMethods,
} from "aws-cdk-lib/aws-stepfunctions-tasks";
import { Construct } from "constructs";

export interface SfnStackProps extends StackProps {
  readonly stageId: string;
  readonly vpc: IVpc;
  readonly dataLake: IBucket;
  readonly ingestJobArn: string;
  readonly jobQueueArn: string;
  readonly airbyte: Cluster;
}

export class SfnStack extends NestedStack {
  constructor(scope: Construct, id: string, props: SfnStackProps) {
    super(scope, id, props);

    const ingestJob = new BatchSubmitJob(this, "mimo-ingest-job", {
      jobDefinitionArn: props.ingestJobArn,
      jobName: `mimo-${props.stageId}-ingest-job`,
      jobQueueArn: props.jobQueueArn,
    });

    const airbyteIngestJob = new EksCall(this, "airbyte-ingest-job", {
      cluster: props.airbyte,
      httpMethod: HttpMethods.POST,
      httpPath: "/api/v1/connections",
    });
  }
}
