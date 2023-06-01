import { Stage, StageProps } from "aws-cdk-lib";
import {
  AuthorizationType,
  ConnectionType,
  Integration,
  IntegrationType,
  VpcLink,
} from "aws-cdk-lib/aws-apigateway";
import {
  GatewayVpcEndpointAwsService,
  InterfaceVpcEndpointAwsService,
  SubnetType,
} from "aws-cdk-lib/aws-ec2";
import { NetworkLoadBalancer } from "aws-cdk-lib/aws-elasticloadbalancingv2";
import { PolicyStatement } from "aws-cdk-lib/aws-iam";
import { Construct } from "constructs";
import { ApiStack } from "./api";
import { CdnStack } from "./cdn";
import { DynamoStack } from "./dynamo";
import { RouteConfig } from "./model";
import { S3Stack } from "./s3";
import { SecretsStack } from "./secrets";
import { ApplicantStack } from "./services/applicant/lambda";
import { CoalescerStack } from "./services/coalescer/stack";
import { ConnectorStack } from "./services/connector/lambda";
import { DetectiveStack } from "./services/detective/lambda";
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
    const connectorService = new ConnectorStack(this, "connector", {
      stageId: props.stageId,
    });
    const detectiveService = new DetectiveStack(this, "detective", {
      stageId: props.stageId,
    });
    const usageMonitorService = new UsageMonitorStack(this, "usage-monitor", {
      stageId: props.stageId,
    });
    const applicantService = new ApplicantStack(this, "applicant", {
      stageId: props.stageId,
    });
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
        dynamo.mimoTable.grantWriteData(method.handler);
      } else {
        throw new Error(`Unknown method: ${method.name}`);
      }
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
    secrets.grantRead(detectiveService.indexLambda);

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

    connectorService.internalParamsLambda.addEnvironment(
      "INTEGRATIONS_PATH",
      integrationsPath
    );
    connectorService.internalParamsLambda.addToRolePolicy(
      new PolicyStatement({
        actions: ["ssm:Describe*", "ssm:Get*", "ssm:List*"],
        resources: ["*"],
      })
    );
    dynamo.mimoTable.grantReadData(connectorService.internalParamsLambda);

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
    }

    const ssm = new SsmStack(this, "ssm", {
      stageId: props.stageId,
    });
    ssm.defineIntegrationParams(integrationsPath, `${assetsPrefixPath}/icons`);
    ssm.defineUsagePlanParams(usagePlansPath, [api.defaultUsagePlan]);
    ssm.defineApiParams(apiPath, api.api);

    if (props.stageId === "beta") {
      const vpc = new VpcStack(this, "vpc", {
        stageId: props.stageId,
      });
      vpc.vpc.addGatewayEndpoint("s3-gateway", {
        service: GatewayVpcEndpointAwsService.S3,
        subnets: [
          {
            subnetType: SubnetType.PRIVATE_ISOLATED,
          },
          {
            subnetType: SubnetType.PRIVATE_WITH_EGRESS,
          },
        ],
      });
      vpc.vpc.addInterfaceEndpoint("ecr-interface", {
        service: InterfaceVpcEndpointAwsService.ECR,
      });
      vpc.vpc.addInterfaceEndpoint("ecr-docker-interface", {
        service: InterfaceVpcEndpointAwsService.ECR_DOCKER,
      });
      vpc.vpc.addInterfaceEndpoint("secrets-interface", {
        service: InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      });
      vpc.vpc.addInterfaceEndpoint("cloudwatch-interface", {
        service: InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
      });

      // const airbyte = getAirbyte(this, props.stageId);

      const coalescer = new CoalescerStack(this, "coalescer", {
        stageId: props.stageId,
        vpc: vpc.vpc,
        indexFunction: detectiveService.indexLambda,
        paramsFunction: connectorService.internalParamsLambda,
      });

      const airbyteNlb = NetworkLoadBalancer.fromNetworkLoadBalancerAttributes(
        api,
        "airbyte-nlb",
        {
          loadBalancerArn: process.env.AIRBYTE_NLB_ARN!,
          loadBalancerDnsName: process.env.AIRBYTE_NLB_DNS_NAME!,
        }
      );
      const vpcLink = new VpcLink(api, "airbyte-vpc-link", {
        vpcLinkName: "vpc-link",
        targets: [airbyteNlb],
      });
      const integration = new Integration({
        type: IntegrationType.HTTP_PROXY,
        options: {
          connectionType: ConnectionType.VPC_LINK,
          vpcLink,
          requestParameters: {
            "integration.request.path.proxy": "method.request.path.proxy",
          },
        },
        integrationHttpMethod: "POST",
        uri: `http://${airbyteNlb.loadBalancerDnsName}:80/{proxy}`,
      });
      const airbyte = api.api.root.addResource("airbyte");
      const proxy = airbyte.addProxy();
      proxy.addMethod("POST", integration, {
        authorizationType: AuthorizationType.NONE,
        requestParameters: {
          "method.request.path.proxy": true,
        },
      });
    }
  }
}
