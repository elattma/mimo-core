import { Stack, StackProps } from "aws-cdk-lib";
import { RestApi } from "aws-cdk-lib/aws-apigateway";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";
import { MimoUsagePlan } from "./model";

type IntegrationId = string;

// TODO: move to some common data model shared with python backend
interface IntegrationConfig {
  id: IntegrationId;
  name: string;
  description: string;
  oauth2_link: string;
  authorize_endpoint: string;
}

// TODO: move to some other representation in a file that's best suited for this type of config
const INTEGRATION_CONFIGS: IntegrationConfig[] = [
  {
    id: "slack_messaging",
    name: "Slack",
    description: "Some description for Slack",
    oauth2_link:
      "https://slack.com/oauth/v2/authorize?scope=groups:history&client_id=3857399127559.4690380022609",
    authorize_endpoint: "https://slack.com/api/oauth.v2.access",
  },
  {
    id: "google_docs",
    name: "Google Docs",
    description: "Some description for Google Docs",
    oauth2_link:
      "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline&prompt=consent",
    authorize_endpoint: "https://oauth2.googleapis.com/token",
  },
  {
    id: "google_mail",
    name: "Google Mail",
    description: "Some description for Gmail",
    oauth2_link:
      "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/gmail.readonly&response_type=code&access_type=offline&prompt=consent",
    authorize_endpoint: "https://oauth2.googleapis.com/token",
  },
  {
    id: "notion_docs",
    name: "Notion Docs",
    description: "Some description for Notion",
    oauth2_link:
      "https://api.notion.com/v1/oauth/authorize?client_id=c23b0a26-4048-4fe6-888b-f6a89ce1caac&response_type=code&owner=user",
    authorize_endpoint: "https://api.notion.com/v1/oauth/token",
  },
  {
    id: "zendesk_support",
    name: "Zendesk Customer Support",
    description: "Some description for Zendesk",
    oauth2_link:
      "https://{subdomain}.zendesk.com/oauth/authorizations/new?response_type=code&client_id=zdg-mimo",
    authorize_endpoint: "https://{subdomain}.zendesk.com/oauth/tokens",
  },
  {
    id: "zoho_crm",
    name: "Zoho CRM",
    description: "Some description for Zoho",
    oauth2_link:
      "https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.coql.READ&client_id=1000.FOXW2IM5QG3WT0PJTJZDW6WJKQ9LEQ&response_type=code&access_type=offline&prompt=consent",
    authorize_endpoint: "https://accounts.zoho.com/oauth/v2/token",
  },
  {
    id: "salesforce_crm",
    name: "Salesforce CRM",
    description: "Some description for Salesforce CRM",
    oauth2_link:
      "https://mimo2-dev-ed.develop.my.salesforce.com/services/oauth2/authorize?client_id=3MVG9gtDqcOkH4PIHJEX7YrYZrqFF1MLN6hTW_dnrQJGc6O23xHsDjXvSerZUMCZwcLxSwifcYUJ0F4Og.ouo&response_type=code&scope=api%20id%20refresh_token",
    authorize_endpoint:
      "https://mimo2-dev-ed.my.salesforce.com/services/oauth2/token",
  },
  {
    id: "intercom_support",
    name: "Intercom Customer Support",
    description: "Some description for Intercom Support",
    oauth2_link: "coming_soon",
    authorize_endpoint: "coming_soon",
  },
  {
    id: "microsoft_mail",
    name: "Outlook Mail",
    description: "Some description for Outlook Mail",
    oauth2_link:
      "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=34742503-198c-4e12-a2e1-2951fa081e72&scope=offline_access%20user.read%20mail.read&response_type=code&response_mode=query",
    authorize_endpoint:
      "https://login.microsoftonline.com/common/oauth2/v2.0/token",
  },
];

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
        // allowedPattern: // TODO: Add allowed patterns
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
        stringValue: `${prefixIconPath}/${integrationConfig.id}.svg`, // TODO: enforce somehow that the icon exists
      });

      new StringParameter(
        this,
        `${integrationConfig.id}-oauth2_link-parameter`,
        {
          parameterName: `${integrationsPath}/${integrationConfig.id}/oauth2_link`,
          stringValue: integrationConfig.oauth2_link,
        }
      );

      new StringParameter(
        this,
        `${integrationConfig.id}-authorize_endpoint-parameter`,
        {
          parameterName: `${integrationsPath}/${integrationConfig.id}/authorize_endpoint`,
          stringValue: integrationConfig.authorize_endpoint,
        }
      );
    });
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
