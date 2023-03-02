import { Stage, StageProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { AppsyncStack } from "./appsync";
import { DynamoStack } from "./dynamo";
import { S3Stack } from "./s3";
import { SsmStack } from "./ssm";

export interface MimoStageProps extends StageProps {
  readonly domainName: string;
  readonly stageId: string;
}

export class MimoStage extends Stage {
  constructor(scope: Construct, id: string, props: MimoStageProps) {
    super(scope, id, props);

    const dynamo = new DynamoStack(this, "dynamo");
    const appsync = new AppsyncStack(this, "appsync");
    const s3 = new S3Stack(this, "s3", {
      stageId: props.stageId,
    });

    const integrationsPath = `/${props.stageId}/mimo/integrations`;
    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
      integrationsPath: integrationsPath,
    });

    // TODO: refactor to split between common and based on api route
    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      mimoTable: dynamo.mimoTable,
      integrationsPath: integrationsPath,
      appsyncApi: appsync.gqlApi,
      uploadItemBucket: s3.uploadItemBucket,
    });
    api.addDependency(ssm);
    api.addDependency(appsync);
    api.addDependency(s3);
  }
}
