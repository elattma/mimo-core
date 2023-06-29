import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://app.hubspot.com/oauth/authorize?client_id=9e3a4051-89bc-4d8a-a626-71fa68e2b9d8&redirect_uri=http://localhost:3000/dashboard/library&scope=crm.lists.read%20crm.objects.contacts.read%20crm.objects.marketing_events.read%20crm.schemas.custom.read%20crm.objects.custom.read%20settings.users.read%20crm.schemas.contacts.read%20cms.domains.read%20cms.functions.read%20crm.objects.feedback_submissions.read%20crm.objects.companies.read%20crm.objects.deals.read%20crm.schemas.companies.read%20crm.schemas.deals.read%20cms.knowledge_base.articles.read%20cms.knowledge_base.settings.read%20crm.objects.owners.read%20settings.users.teams.read%20crm.objects.quotes.read%20crm.schemas.quotes.read%20crm.objects.line_items.read%20crm.schemas.line_items.read%20cms.performance.read%20settings.currencies.read%20crm.objects.goals.read",
  authorize_endpoint: "https://api.hubapi.com/oauth/v1/token",
  refresh_endpoint: "https://api.hubapi.com/oauth/v1/token",
  client_id: "9e3a4051-89bc-4d8a-a626-71fa68e2b9d8",
  enforce_secrets: ["client_secret"],
};

const hubspotIntegrationConfig: IntegrationConfig = {
  id: "hubspot",
  name: "HubSpot",
  description: "Some description for Hubspot",
  auth_strategies: [tokenOAuth2Strategy],
};

export default hubspotIntegrationConfig;
