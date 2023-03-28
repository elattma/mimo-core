import { Stack, StackProps } from "aws-cdk-lib";
import { StringParameter } from "aws-cdk-lib/aws-ssm";
import { Construct } from "constructs";

type IntegrationId = string;

// TODO: move to some common data model shared with python backend
interface IntegrationConfig {
  id: IntegrationId;
  name: string;
  description: string;
  oauth2_link: string;
  type?: string; // TODO: switch to the same enum used by the backend
}

// TODO: add fixed redirect_uri
// TODO: move to some other representation in a file that's best suited for this type of config
const INTEGRATION_CONFIGS: IntegrationConfig[] = [
  {
    id: "slack",
    name: "Slack",
    description: "Some description for Slack",
    oauth2_link:
      "https://slack.com/oauth/v2/authorize?scope=groups:history&client_id=3857399127559.4690380022609",
  },
  {
    id: "google_docs",
    name: "Google Docs",
    description: "Some description for Google Docs",
    oauth2_link:
      "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline&prompt=consent",
  },
  {
    id: "google_mail",
    name: "Gmail",
    description: "Some description for Gmail",
    oauth2_link:
      "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/gmail.readonly&response_type=code&access_type=offline&prompt=consent",
  },
  {
    id: "notion",
    name: "Notion",
    description: "Some description for Notion",
    oauth2_link:
      "https://api.notion.com/v1/oauth/authorize?client_id=c23b0a26-4048-4fe6-888b-f6a89ce1caac&response_type=code&owner=user",
  },
  {
    id: "zendesk",
    name: "Zendesk",
    description: "Some description for Zendesk",
    oauth2_link:
      "https://mimo845.zendesk.com/oauth/authorizations/new?response_type=code&client_id=14311603347725&scope=read",
  },
  {
    id: "zoho",
    name: "Zoho",
    description: "Some description for Zoho",
    oauth2_link:
      "https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.coql.READ&client_id=1000.FOXW2IM5QG3WT0PJTJZDW6WJKQ9LEQ&response_type=code&access_type=offline&prompt=consent",
  },
];

export interface SsmStackProps extends StackProps {
  readonly stageId: string;
  readonly integrationsPath: string;
  readonly prefixIconPath: string;
}

export class SsmStack extends Stack {
  constructor(scope: Construct, id: string, props: SsmStackProps) {
    super(scope, id, props);

    INTEGRATION_CONFIGS.forEach((integrationConfig: IntegrationConfig) => {
      this.defineIntegrationParams(
        integrationConfig,
        props.integrationsPath,
        props.prefixIconPath
      );
    });
  }

  defineIntegrationParams = (
    integrationConfig: IntegrationConfig,
    integrationsPath: string,
    prefixIconPath: string
  ) => {
    new StringParameter(this, `${integrationConfig.id}-id-parameter`, {
      // allowedPattern: // TODO: Add allowed patterns
      parameterName: `${integrationsPath}/${integrationConfig.id}/id`,
      stringValue: integrationConfig.id,
    });

    new StringParameter(this, `${integrationConfig.id}-name-parameter`, {
      parameterName: `${integrationsPath}/${integrationConfig.id}/name`,
      stringValue: integrationConfig.name,
    });

    new StringParameter(this, `${integrationConfig.id}-description-parameter`, {
      parameterName: `${integrationsPath}/${integrationConfig.id}/description`,
      stringValue: integrationConfig.description,
    });

    new StringParameter(this, `${integrationConfig.id}-icon-parameter`, {
      parameterName: `${integrationsPath}/${integrationConfig.id}/icon`,
      stringValue: `${prefixIconPath}/${integrationConfig.id}.svg`, // TODO: enforce somehow that the icon exists
    });

    new StringParameter(this, `${integrationConfig.id}-oauth2_link-parameter`, {
      parameterName: `${integrationsPath}/${integrationConfig.id}/oauth2_link`,
      stringValue: integrationConfig.oauth2_link,
    });

    // TODO: add type
  };
}
