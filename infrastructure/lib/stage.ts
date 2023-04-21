import { Stage, StageProps } from "aws-cdk-lib";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { AppsyncStack } from "./appsync";
import { CdnStack } from "./cdn";
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

    const assetsPrefixPath = `assets.${props.domainName}`;
    new CdnStack(this, "cdn", {
      stageId: props.stageId,
      assetsBucket: s3.assetsBucket,
      domainName: assetsPrefixPath,
    });

    const integrationsPath = `/${props.stageId}/mimo/integrations`;
    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
      integrationsPath: integrationsPath,
      prefixIconPath: `${assetsPrefixPath}/icons`,
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
    for (const handler of api.usagePlanHandlers) {
      handler.addEnvironment(
        "DEFAULT_USAGE_PLAN_ID",
        api.defaultUsagePlan.usagePlanId
      );
      handler.addToRolePolicy(
        new PolicyStatement({
          actions: [
            "apigateway:GET",
            "apigateway:PUT",
            "apigateway:POST",
            "apigateway:DELETE",
          ],
          resources: ["*"],
        })
      );
    }
  }
}
