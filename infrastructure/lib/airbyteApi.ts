import { Stack, StackProps } from "aws-cdk-lib";
import {
  AccessLogFormat,
  ApiKeySourceType,
  AuthorizationType,
  ConnectionType,
  Integration,
  IntegrationType,
  LogGroupLogDestination,
  MethodLoggingLevel,
  RestApi,
  VpcLink,
} from "aws-cdk-lib/aws-apigateway";
import { NetworkLoadBalancer } from "aws-cdk-lib/aws-elasticloadbalancingv2";
import { LogGroup } from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";

export interface AirbyteApiStackProps extends StackProps {
  readonly stageId: string;
}

export class AirbyteApiStack extends Stack {
  readonly api: RestApi;

  constructor(scope: Construct, id: string, props: AirbyteApiStackProps) {
    super(scope, id, props);

    this.api = this.getRestApi(props.stageId);
    this.getAirbyte();
  }

  getRestApi = (stageId: string): RestApi => {
    const api = new RestApi(this, `mimo-airbyteapi`, {
      apiKeySourceType: ApiKeySourceType.AUTHORIZER,
      deployOptions: {
        accessLogDestination: new LogGroupLogDestination(
          new LogGroup(this, `${stageId}-airbyteapi-access-log`)
        ),
        accessLogFormat: AccessLogFormat.jsonWithStandardFields(),
        loggingLevel: MethodLoggingLevel.INFO,
      },
    });

    return api;
  };

  getAirbyte = () => {
    const airbyteLB = NetworkLoadBalancer.fromNetworkLoadBalancerAttributes(
      this,
      "mimo-airbyteload-balancer",
      {
        loadBalancerArn: process.env.AIRBYTE_LB_ARN!,
        loadBalancerDnsName: process.env.AIRBYTE_LB_DNS_NAME!,
      }
    );
    const vpcLink = new VpcLink(this, "mimo-airbytevpc-link", {
      vpcLinkName: "vpc-link",
      targets: [airbyteLB],
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
      integrationHttpMethod: "ANY",
      uri: `http://${airbyteLB.loadBalancerDnsName}:80/{proxy}`,
    });
    const airbyte = this.api.root.addResource("airbyte");
    airbyte.addProxy({
      defaultIntegration: integration,
      defaultMethodOptions: {
        authorizationType: AuthorizationType.NONE,
        requestParameters: {
          "method.request.path.proxy": true,
        },
      },
    });
  };
}
