import { Stack, StackProps } from "aws-cdk-lib";
import { Bucket, HttpMethods, IBucket } from "aws-cdk-lib/aws-s3";
import { BucketDeployment, Source } from "aws-cdk-lib/aws-s3-deployment";
import { Construct } from "constructs";
import * as path from "path";

export interface S3StackProps extends StackProps {
  readonly stageId: string;
}

export class S3Stack extends Stack {
  readonly uploadBucket: IBucket;
  readonly assetsBucket: IBucket;
  readonly dataLake: IBucket;

  constructor(scope: Construct, id: string, props: S3StackProps) {
    super(scope, id, props);

    this.uploadBucket = new Bucket(this, "upload-bucket", {
      bucketName: `mimo-${props.stageId}-upload`,
      // TODO: add? enforceSSL: true,
      cors: [
        {
          allowedHeaders: ["*"],
          allowedOrigins: [
            "https://www.mimo.team",
            "https://mimo.team",
            "https://*.mimo.team",
            "http://localhost:3000",
          ],
          allowedMethods: [HttpMethods.PUT],
        },
      ], // TODO: fix to just mimo.team
    });

    this.assetsBucket = new Bucket(this, "assets-bucket", {
      bucketName: `mimo-${props.stageId}-assets`,
    });

    this.dataLake = Bucket.fromBucketName(
      this,
      "data-lake",
      `mimo-${props.stageId}-data-lake`
    );

    new BucketDeployment(this, "icons-deployment", {
      sources: [Source.asset(path.join(__dirname, "./integrations/icons"))],
      destinationBucket: this.assetsBucket,
      destinationKeyPrefix: "icons",
    });

    new BucketDeployment(this, "logos-deployment", {
      sources: [Source.asset(path.join(__dirname, "./logos"))],
      destinationBucket: this.assetsBucket,
      destinationKeyPrefix: "logos",
    });
  }
}
