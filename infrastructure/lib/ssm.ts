import { Stack, StackProps } from "aws-cdk-lib";
import { RestApi } from "aws-cdk-lib/aws-apigateway";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";
import { INTEGRATION_CONFIGS } from "./integrations";
import {
  AuthType,
  IntegrationConfig,
  TokenOAuth2AuthStrategy,
} from "./integrations/model";
import { MimoUsagePlan } from "./model";

export interface SsmStackProps extends StackProps {
  readonly stageId: string;
}

export class SsmStack extends Stack {
  constructor(scope: Construct, id: string, props: SsmStackProps) {
    super(scope, id, props);
  }

  defineIntegrationParams = (
    integrationsPath: string,
    prefixIconPath: string
  ) => {
    INTEGRATION_CONFIGS.forEach((integrationConfig: IntegrationConfig) => {
      new StringParameter(this, `${integrationConfig.id}-id-parameter`, {
        parameterName: `${integrationsPath}/${integrationConfig.id}/id`,
        stringValue: integrationConfig.id,
      });

      new StringParameter(this, `${integrationConfig.id}-name-parameter`, {
        parameterName: `${integrationsPath}/${integrationConfig.id}/name`,
        stringValue: integrationConfig.name,
      });

      new StringParameter(
        this,
        `${integrationConfig.id}-description-parameter`,
        {
          parameterName: `${integrationsPath}/${integrationConfig.id}/description`,
          stringValue: integrationConfig.description,
        }
      );

      new StringParameter(this, `${integrationConfig.id}-icon-parameter`, {
        parameterName: `${integrationsPath}/${integrationConfig.id}/icon`,
        stringValue: `https://${prefixIconPath}/${integrationConfig.id}.svg`, // TODO: enforce somehow that the icon exists
      });

      for (const authStrategy of integrationConfig.auth_strategies) {
        const authPrefix = `${integrationsPath}/${
          integrationConfig.id
        }/auth_strategies/${authStrategy.type.toString()}`;
        if (authStrategy.type === AuthType.TOKEN_OAUTH2) {
          this.defineTokenOAuth2AuthStrategyParams(
            authPrefix,
            authStrategy as TokenOAuth2AuthStrategy
          );
        } else if (authStrategy.type === AuthType.TOKEN_DIRECT) {
          new StringParameter(this, `${authPrefix}-token_endpoint-parameter`, {
            parameterName: `${authPrefix}/id`,
            stringValue: authStrategy.type.toString(),
          });
        }
      }
    });
  };

  defineTokenOAuth2AuthStrategyParams = (
    authPrefix: string,
    authStrategy: TokenOAuth2AuthStrategy
  ) => {
    new StringParameter(this, `${authPrefix}-oauth2_link-parameter`, {
      parameterName: `${authPrefix}/oauth2_link`,
      stringValue: authStrategy.oauth2_link,
    });

    new StringParameter(this, `${authPrefix}-authorize_endpoint-parameter`, {
      parameterName: `${authPrefix}/authorize_endpoint`,
      stringValue: authStrategy.authorize_endpoint,
    });

    new StringParameter(this, `${authPrefix}-client_id-parameter`, {
      parameterName: `${authPrefix}/client_id`,
      stringValue: authStrategy.client_id,
    });

    if (authStrategy.refresh_endpoint) {
      new StringParameter(this, `${authPrefix}-refresh_endpoint-parameter`, {
        parameterName: `${authPrefix}/refresh_endpoint`,
        stringValue: authStrategy.refresh_endpoint,
      });
    }

    this.enforceSecrets(authPrefix, authStrategy.enforce_secrets);
  };

  enforceSecrets = (prefix: string, enforceList: string[]) => {
    for (const secret of enforceList) {
      const param = StringParameter.fromSecureStringParameterAttributes(
        this,
        `${prefix}/${secret}-parameter`,
        { parameterName: `${prefix}/${secret}` }
      );
      if (param.stringValue === undefined) {
        throw new Error(
          `Secret ${secret} is not defined in the SSM Parameter Store`
        );
      }
    }
  };

  defineUsagePlanParams = (
    usagePlanPath: string,
    usagePlans: MimoUsagePlan[]
  ) => {
    for (const usagePlan of usagePlans) {
      new StringParameter(this, `usageplan-${usagePlan.name}-id-parameter`, {
        parameterName: `${usagePlanPath}/${usagePlan.name}/id`,
        stringValue: usagePlan.plan.usagePlanId,
      });
    }
  };

  defineApiParams = (apiPath: string, api: RestApi) => {
    new StringParameter(this, `api-id-parameter`, {
      parameterName: `${apiPath}/id`,
      stringValue: api.restApiId,
    });
  };
}
