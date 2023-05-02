import googleDocs from "./config/google_docs";
import googleMail from "./config/google_mail";
import intercomSupport from "./config/intercom_support";
import microsoftMail from "./config/microsoft_mail";
import notionDocs from "./config/notion_docs";
import salesforceCrm from "./config/salesforce_crm";
import slackMessaging from "./config/slack_messaging";
import zendeskSupport from "./config/zendesk_support";
import zohoCrm from "./config/zoho_crm";
import { IntegrationConfig } from "./model";

export const INTEGRATION_CONFIGS: IntegrationConfig[] = [
  slackMessaging,
  googleDocs,
  googleMail,
  notionDocs,
  zendeskSupport,
  zohoCrm,
  salesforceCrm,
  intercomSupport,
  microsoftMail,
];
