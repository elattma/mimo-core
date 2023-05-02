import { Stack, StackProps } from "aws-cdk-lib";
import { Bucket, HttpMethods, IBucket } from "aws-cdk-lib/aws-s3";
import { BucketDeployment, Source } from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";
import * as path from "path";

export interface S3StackProps extends StackProps {
  readonly stageId: string;
}

export class S3Stack extends Stack {
  readonly uploadItemBucket: IBucket;
  readonly assetsBucket: IBucket;

  constructor(scope: Construct, id: string, props: S3StackProps) {
    super(scope, id, props);

    this.uploadItemBucket = new Bucket(this, "upload-item-bucket", {
      bucketName: `mimo-${props.stageId}-upload-item`,
      // TODO: add? enforceSSL: true,
      cors: [
        {
          allowedOrigins: ["*"],
          allowedMethods: [HttpMethods.PUT],
        },
      ], // TODO: fix to just mimo.team
    });

    this.assetsBucket = new Bucket(this, "assets-bucket", {
      bucketName: `mimo-${props.stageId}-assets`,
    });

    new BucketDeployment(this, "icons-deployment", {
      sources: [Source.asset(path.join(__dirname, "./integrations/icons"))],
      destinationBucket: this.assetsBucket,
      destinationKeyPrefix: "icons",
    });
  }
}
