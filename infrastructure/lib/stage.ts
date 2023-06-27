import { Stage, StageProps } from "aws-cdk-lib";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { AirbyteApiStack } from "./airbyteApi";
import { ApiStack } from "./api";
import { CdnStack } from "./cdn";
import { DynamoStack } from "./dynamo";
import { RouteConfig } from "./model";
import { S3Stack } from "./s3";
import { SecretsStack } from "./secrets";
import { ApplicantStack } from "./services/applicant/lambda";
import { ConnectorStack } from "./services/connector/stack";
import { DetectiveStack } from "./services/detective/stack";
import { UsageMonitorStack } from "./services/usage_monitor/lambda";
import { SsmStack } from "./ssm";
import { VpcStack } from "./vpc";

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
    const vpc = new VpcStack(this, "vpc", {
      stageId: props.stageId,
    });

    const airbyteApi = new AirbyteApiStack(this, "airbyteapi", {
      stageId: props.stageId,
    });

    const detectiveService = new DetectiveStack(this, "detective", {
      stageId: props.stageId,
      vpc: vpc.vpc,
    });
    const connectorService = new ConnectorStack(this, "connector", {
      stageId: props.stageId,
      airbyteApi: airbyteApi.api,
      mimoTable: dynamo.mimoTable,
      vpc: vpc.vpc,
      uploadBucket: s3.uploadBucket,
    });
    const usageMonitorService = new UsageMonitorStack(this, "usage-monitor", {
      stageId: props.stageId,
    });
    const applicantService = new ApplicantStack(this, "applicant", {
      stageId: props.stageId,
    });
    if (
      !(
        connectorService.definition.container.jobRole &&
        connectorService.graphPlotDefinition.container.jobRole
      )
    ) {
      throw new Error("jobRole is required");
    }
    s3.dataLake.grantReadWrite(connectorService.definition.container.jobRole);
    s3.dataLake.grantReadWrite(
      connectorService.graphPlotDefinition.container.jobRole
    );
    s3.uploadBucket.grantRead(connectorService.definition.container.jobRole);

    routeConfigs.push({
      path: "connection",
      methods: connectorService.methods,
      idResource: "connection",
      subRoutes: [
        {
          path: "integration",
          methods: connectorService.integrationMethods,
        },
        {
          path: "user_library",
          methods: connectorService.libraryMethods,
          idResource: "library",
        },
        {
          path: "sync",
          methods: [connectorService.syncMethod],
        },
        {
          path: "upload",
          methods: [connectorService.uploadMethod],
        },
      ],
    });
    routeConfigs.push({
      path: "v1",
      subRoutes: [
        {
          path: "context",
          methods: detectiveService.methods,
        },
        {
          path: "auth",
          methods: applicantService.v1AuthMethods,
        },
        {
          path: "library",
          methods: applicantService.v1LibraryMethods,
        },
      ],
    });
    routeConfigs.push({
      path: "v0",
      subRoutes: [
        {
          path: "context",
          methods: [detectiveService.v0GetContextMethod],
        },
      ],
    });
    routeConfigs.push({
      path: "usage",
      methods: usageMonitorService.methods,
    });
    routeConfigs.push({
      path: "app",
      methods: applicantService.appMethods,
      idResource: "app",
      subRoutes: [
        {
          path: "auth",
          methods: applicantService.authMethods.reverse(),
        },
        {
          path: "api_key",
          methods: applicantService.apiKeyMethods,
        },
        {
          path: "developer",
          methods: applicantService.developerMethods,
        },
      ],
    });
    const api = new ApiStack(this, "api", {
      stageId: props.stageId,
      domainName: props.domainName,
      routeConfigs: routeConfigs,
    });

    dynamo.mimoTable.grantReadData(api.apiKeyLambda);
    api.apiKeyLambda.addToRolePolicy(
      new PolicyStatement({
        actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
        resources: ["*"],
      })
    );
    s3.uploadBucket.grantReadWrite(connectorService.uploadMethod.handler);

    for (const method of connectorService.methods) {
      method.handler.addEnvironment("INTEGRATIONS_PATH", integrationsPath);
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: ["*"],
        })
      );
      if (method.name === "GET") {
        dynamo.mimoTable.grantReadData(method.handler);
      } else if (method.name === "POST") {
        dynamo.mimoTable.grantWriteData(method.handler);
      } else if (method.name === "DELETE") {
        dynamo.mimoTable.grantReadWriteData(method.handler);
      } else {
        throw new Error(`Unknown method: ${method.name}`);
      }
      // add policy to call api gateway airbyte api
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["execute-api:Invoke"],
          resources: [airbyteApi.api.arnForExecuteApi()],
        })
      );
    }

    for (const method of connectorService.libraryMethods) {
      dynamo.mimoTable.grantReadWriteData(method.handler);
    }
    for (const method of applicantService.v1LibraryMethods) {
      dynamo.mimoTable.grantReadData(method.handler);
    }
    for (const method of detectiveService.methods) {
      secrets.grantRead(method.handler);
    }
    secrets.grantRead(detectiveService.v0GetContextMethod.handler);

    for (const method of connectorService.integrationMethods) {
      secrets.grantRead(method.handler);
      method.handler.addEnvironment("INTEGRATIONS_PATH", integrationsPath);
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: ["*"],
        })
      );
    }

    for (const method of usageMonitorService.methods) {
      method.handler.addEnvironment("API_PATH", apiPath);
      method.handler.addEnvironment("USAGE_PLANS_PATH", usagePlansPath);
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: ["*"],
        })
      );
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["apigateway:GET"],
          resources: ["*"],
        })
      );
    }

    for (const method of [
      ...applicantService.appMethods,
      ...applicantService.authMethods,
      ...applicantService.v1AuthMethods,
    ]) {
      if (method.name === "GET") {
        dynamo.mimoTable.grantReadData(method.handler);
      } else if (method.name === "POST") {
        dynamo.mimoTable.grantReadWriteData(method.handler);
      } else if (method.name === "DELETE") {
        dynamo.mimoTable.grantWriteData(method.handler);
      }
    }

    for (const method of applicantService.apiKeyMethods) {
      if (method.name === "GET") {
        dynamo.mimoTable.grantReadData(method.handler);
      } else if (method.name === "POST") {
        dynamo.mimoTable.grantReadWriteData(method.handler);
      } else if (method.name === "DELETE") {
        dynamo.mimoTable.grantWriteData(method.handler);
      }
    }

    for (const method of applicantService.developerMethods) {
      method.handler.addToRolePolicy(
        new PolicyStatement({
          actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
          resources: ["*"],
        })
      );
      if (method.name === "PATCH") {
        method.handler.addToRolePolicy(
          new PolicyStatement({
            actions: ["ssm:PutParameter"],
            resources: ["*"],
          })
        );
      }
      if (method.name === "POST") {
        dynamo.waitlistTable.grantWriteData(method.handler);
      }
      if (method.name === "GET") {
        dynamo.waitlistTable.grantReadData(method.handler);
      }
    }

    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
    });
    ssm.defineIntegrationParams(integrationsPath, `${assetsPrefixPath}/icons`);
    ssm.defineUsagePlanParams(usagePlansPath, [api.defaultUsagePlan]);
    ssm.defineApiParams(apiPath, api.api);
  }
}
