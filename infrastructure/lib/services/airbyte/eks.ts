import {
  ArgoCDAddOn,
  AwsLoadBalancerControllerAddOn,
  CalicoOperatorAddOn,
  ClusterAutoScalerAddOn,
  ClusterInfo,
  CoreDnsAddOn,
  EbsCsiDriverAddOn,
  EksBlueprint,
  GlobalResources,
  HelmAddOn,
  HelmAddOnUserProps,
  KubeProxyAddOn,
  MetricsServerAddOn,
  ResourceContext,
  ResourceProvider,
  VpcCniAddOn,
} from "@aws-quickstart/eks-blueprints";
import {
  IVpc,
  Vpc,
} from "@aws-quickstart/eks-blueprints/node_modules/aws-cdk-lib/aws-ec2/lib/vpc";
import { IpAddresses, SubnetType } from "aws-cdk-lib/aws-ec2";
import { Construct } from "constructs";

export interface AirbyteAddOnProps extends HelmAddOnUserProps {}

const defaultProps = {
  name: "airbyte",
  namespace: "kube-system",
  version: "0.45.20",
  chart: "airbyte",
  release: "airbyte",
  repository: "https://airbytehq.github.io/helm-charts",
};

class AirbyteAddOn extends HelmAddOn {
  private options: AirbyteAddOnProps;

  constructor(props?: AirbyteAddOnProps) {
    super({ ...defaultProps, ...props });
    this.options = this.props;
  }

  deploy(clusterInfo: ClusterInfo): void | Promise<Construct> {
    const cluster = clusterInfo.cluster;
    let values = this.options.values ?? {};
    const helmChart = this.addHelmChart(clusterInfo, {}, false, false);
    return Promise.resolve(helmChart);
  }
}

export const getAirbyte = (scope: Construct, stage: string): EksBlueprint => {
  const blueprint = EksBlueprint.builder()
    .addOns(
      new ClusterAutoScalerAddOn(),
      new EbsCsiDriverAddOn(),
      new ArgoCDAddOn(),
      new CalicoOperatorAddOn(),
      new MetricsServerAddOn(),
      new AwsLoadBalancerControllerAddOn(),
      new VpcCniAddOn(),
      new CoreDnsAddOn(),
      new KubeProxyAddOn(),
      new AirbyteAddOn()
    )
    .resourceProvider(
      GlobalResources.Vpc,
      new (class implements ResourceProvider<IVpc> {
        provide(context: ResourceContext): IVpc {
          return new Vpc(context.scope, "eks-vpc", {
            ipAddresses: IpAddresses.cidr("10.0.0.0/16"),
            availabilityZones: ["us-east-1a", "us-east-1b"],
            subnetConfiguration: [
              {
                cidrMask: 24,
                name: "eks-private",
                subnetType: SubnetType.PRIVATE_WITH_EGRESS,
              },
              {
                cidrMask: 24,
                name: "eks-public",
                subnetType: SubnetType.PUBLIC,
              },
            ],
            natGatewaySubnets: {
              availabilityZones: ["us-east-1a"],
              subnetType: SubnetType.PUBLIC,
            },
          });
        }
      })()
    )
    .account("222250063412")
    .region("us-east-1")
    .build(scope, "mimoairbyte");
  return blueprint;
};
