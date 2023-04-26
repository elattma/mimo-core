import { Stage, StageProps } from "aws-cdk-lib";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { CdnStack } from "./cdn";
import { DynamoStack } from "./dynamo";
import { RouteConfig } from "./model";
import { S3Stack } from "./s3";
import { SecretsStack } from "./secrets";
import { ConnectorStack } from "./services/connector/lambda";
import { DetectiveStack } from "./services/detective/lambda";
import { LocksmithStack } from "./services/locksmith/lambda";
import { SsmStack } from "./ssm";

export interface MimoStageProps extends StageProps {
  readonly domainName: string;
  readonly stageId: string;
}

export class MimoStage extends Stage {
  constructor(scope: Construct, id: string, props: MimoStageProps) {
    super(scope, id, props);

    const dynamo = new DynamoStack(this, "dynamo", {
      stageId: props.stageId,
    });
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
    const secrets = new SecretsStack(this, "secrets", {
      stageId: props.stageId,
    });

    const integrationsPath = `/${props.stageId}/integrations`;
    const usagePlansPath = `/${props.stageId}/usage_plans`;
    const apiPath = `/${props.stageId}/api`;

    const routeConfigs: RouteConfig[] = [];
    const locksmithService = new LocksmithStack(this, "locksmith", {
      stageId: props.stageId,
    });
    const connectorService = new ConnectorStack(this, "connector", {
      stageId: props.stageId,
    });
    const detectiveService = new DetectiveStack(this, "detective", {
      stageId: props.stageId,
    });
    routeConfigs.push({
      path: "locksmith",
      methods: locksmithService.methods,
    });
    routeConfigs.push({
      path: "connector",
      methods: connectorService.methods,
      subRoutes: [
        {
          path: "integration",
          methods: connectorService.integrationMethods,
        },
      ],
    });
    routeConfigs.push({
      path: "context",
      methods: detectiveService.methods,
    });
    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      routeConfigs: routeConfigs,
    });

    for (const method of connectorService.methods) {
      if (method.name === "GET") {
        dynamo.mimoTable.grantReadData(method.handler);
      } else if (method.name === "POST") {
        dynamo.mimoTable.grantWriteData(method.handler);
      } else if (method.name === "DELETE") {
        dynamo.mimoTable.grantWriteData(method.handler);
      } else {
        throw new Error(`Unknown method: ${method.name}`);
      }
    }

    for (const method of detectiveService.methods) {
      secrets.grantRead(method.handler);
    }

    for (const method of connectorService.integrationMethods) {
      secrets.grantRead(method.handler);
      method.handler.addEnvironment("INTEGRATIONS_PATH", integrationsPath);
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: [`*`],
        })
      );
    }

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
