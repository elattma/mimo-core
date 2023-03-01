import { Stage, StageProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { AppsyncStack } from "./appsync";
import { DynamoStack } from "./dynamo";
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

    const integrationsPath = `/${props.stageId}/mimo/integrations`;
    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
      integrationsPath: integrationsPath,
    });

    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      mimoTable: dynamo.mimoTable,
      integrationsPath: integrationsPath,
      appsyncApi: appsync.gqlApi,
    });
    api.addDependency(ssm);
    api.addDependency(appsync);
  }
}
