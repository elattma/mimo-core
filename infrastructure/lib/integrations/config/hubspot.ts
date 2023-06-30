import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://app.hubspot.com/oauth/authorize?client_id=9e3a4051-89bc-4d8a-a626-71fa68e2b9d8&scope=content%20automation%20forms%20tickets%20e-commerce%20sales-email-read%20crm.lists.read%20crm.objects.contacts.read%20crm.objects.companies.read%20crm.objects.deals.read%20crm.schemas.companies.read%20crm.schemas.deals.read%20crm.objects.owners.read",
  authorize_endpoint: "https://api.hubapi.com/oauth/v1/token",
  refresh_endpoint: "https://api.hubapi.com/oauth/v1/token",
  client_id: "9e3a4051-89bc-4d8a-a626-71fa68e2b9d8",
  enforce_secrets: ["client_secret"],
};

const hubspotIntegrationConfig: IntegrationConfig = {
  id: "hubspot",
  name: "HubSpot",
  description: "Some description for Hubspot",
  airbyte_id: "36c891d9-4bd9-43ac-bad2-10e12756272c",
  auth_strategies: [tokenOAuth2Strategy],
};

export default hubspotIntegrationConfig;
