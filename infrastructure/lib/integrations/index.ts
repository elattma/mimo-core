import asana from "./config/asana";
import clickup from "./config/clickup";
import googleDocs from "./config/google_docs";
import googleMail from "./config/google_mail";
import hubspot from "./config/hubspot";
import intercomSupport from "./config/intercom_support";
import jira from "./config/jira";
import linear from "./config/linear";
import mailchimp from "./config/mailchimp";
import microsoftMail from "./config/microsoft_mail";
import monday from "./config/monday";
import notionDocs from "./config/notion_docs";
import pipedrive from "./config/pipedrive";
import salesforceCrm from "./config/salesforce_crm";
import slackMessaging from "./config/slack_messaging";
import uploadFile from "./config/upload_file";
import webLink from "./config/web_link";
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
  uploadFile,
  webLink,
  hubspot,
  asana,
  jira,
  monday,
  mailchimp,
  linear,
  clickup,
  pipedrive,
];
