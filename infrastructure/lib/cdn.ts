import { Stack, StackProps } from "aws-cdk-lib";
import {
  Certificate,
  CertificateValidation,
} from "aws-cdk-lib/aws-certificatemanager";
import { Distribution } from "aws-cdk-lib/aws-cloudfront";
import { S3Origin } from "aws-cdk-lib/aws-cloudfront-origins";
import { IBucket } from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export interface CdnStackProps extends StackProps {
  readonly stageId: string;
  readonly assetsBucket: IBucket;
  readonly domainName: string;
}

export class CdnStack extends Stack {
  readonly uploadItemBucket: IBucket;
  readonly assetsBucket: IBucket;

  constructor(scope: Construct, id: string, props: CdnStackProps) {
    super(scope, id, props);

    const certificate = new Certificate(this, "cdn-certificate", {
      domainName: props.domainName,
      validation: CertificateValidation.fromDns(),
    });

    new Distribution(this, "cdn", {
      defaultBehavior: { origin: new S3Origin(props.assetsBucket) },
      domainNames: [props.domainName],
      certificate: certificate,
    });
  }
}
