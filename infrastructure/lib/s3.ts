import { Stack, StackProps } from "aws-cdk-lib";
import {
  Bucket,
  BucketEncryption,
  HttpMethods,
  IBucket,
} from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export interface S3StackProps extends StackProps {
  readonly stageId: string;
}

export class S3Stack extends Stack {
  readonly uploadItemBucket: IBucket;

  constructor(scope: Construct, id: string, props: S3StackProps) {
    super(scope, id, props);

    this.uploadItemBucket = new Bucket(this, "upload-item-bucket", {
      bucketName: `${props.stageId}-upload-item`,
      publicReadAccess: false,
      // TODO: add? enforceSSL: true,
      bucketKeyEnabled: true,
      cors: [
        {
          allowedOrigins: ["*"],
          allowedMethods: [HttpMethods.PUT],
        },
      ], // TODO: fix to just mimo.team
      encryption: BucketEncryption.KMS,
    });
  }
}
