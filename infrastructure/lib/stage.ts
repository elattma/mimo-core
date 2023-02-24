import { Stage, StageProps } from "aws-cdk-lib";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { DynamoStack } from "./dynamo";

export interface MimoStageProps extends StageProps {
  readonly domainName: string;
  readonly stageId: string;
}

export class MimoStage extends Stage {
  constructor(scope: Construct, id: string, props: MimoStageProps) {
    super(scope, id, props);

    const dynamo = new DynamoStack(this, "dynamo");

    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      mimoTable: dynamo.mimoTable,
    });
  }
}
