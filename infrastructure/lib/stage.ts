import { Stage, StageProps } from "aws-cdk-lib";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { CdnStack } from "./cdn";
import { RouteConfig } from "./model";
import { S3Stack } from "./s3";
import { LocksmithStack } from "./services/locksmith/lambda";
import { SsmStack } from "./ssm";

export interface MimoStageProps extends StageProps {
  readonly domainName: string;
  readonly stageId: string;
}

export class MimoStage extends Stage {
  constructor(scope: Construct, id: string, props: MimoStageProps) {
    super(scope, id, props);

    // const dynamo = new DynamoStack(this, "dynamo");
    // const appsync = new AppsyncStack(this, "appsync");
    const s3 = new S3Stack(this, "s3", {
      stageId: props.stageId,
    });

    const assetsPrefixPath = `assets.${props.domainName}`;
    if (props.stageId === "beta") {
      new CdnStack(this, "cdn", {
        stageId: props.stageId,
        assetsBucket: s3.assetsBucket,
        domainName: assetsPrefixPath,
      });
    }

    const integrationsPath = `/${props.stageId}/integrations`;
    const usagePlansPath = `/${props.stageId}/usage_plans`;
    const apiPath = `/${props.stageId}/api`;

    // const layer = new LayerStack(this, "layer", {
    //   stageId: props.stageId,
    // });

    const routeConfigs: RouteConfig[] = [];
    const locksmithService = new LocksmithStack(this, "locksmith", {
      stageId: props.stageId,
      // layers: layer.layers,
    });
    routeConfigs.push({
      path: "locksmith",
      methods: locksmithService.methods,
    });
    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      routeConfigs: routeConfigs,
    });
    for (const method of locksmithService.methods) {
      method.handler.addEnvironment("API_PATH", apiPath);
      method.handler.addEnvironment("USAGE_PLANS_PATH", usagePlansPath);
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: [`*`],
        })
      );
    }

    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
    });
    ssm.defineIntegrationParams(integrationsPath, `${assetsPrefixPath}/icons`);
    ssm.defineUsagePlanParams(usagePlansPath, [api.defaultUsagePlan]);
    ssm.defineApiParams(apiPath, api.api);
  }
}
