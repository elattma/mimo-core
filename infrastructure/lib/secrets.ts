import { Stack, StackProps } from "aws-cdk-lib";
import { IGrantable } from "aws-cdk-lib/aws-iam";
import { ISecret, Secret } from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";

export interface SecretsStackProps extends StackProps {
  readonly stageId: string;
}

export class SecretsStack extends Stack {
  readonly integrationsSecret: ISecret;

  constructor(scope: Construct, id: string, props: SecretsStackProps) {
    super(scope, id, props);

    const integrationSecretName = `${props.stageId}/Mimo/Integrations`;
    this.integrationsSecret = Secret.fromSecretNameV2(
      this,
      "integrations-secret",
      integrationSecretName
    );
  }

  grantRead(grantable: IGrantable) {
    this.integrationsSecret.grantRead(grantable);
  }
}
