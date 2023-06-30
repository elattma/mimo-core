import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://login.salesforce.com/services/oauth2/authorize?client_id=3MVG9gtDqcOkH4PIHJEX7YrYZrqFF1MLN6hTW_dnrQJGc6O23xHsDjXvSerZUMCZwcLxSwifcYUJ0F4Og.ouo&response_type=code&scope=api%20id%20refresh_token",
  authorize_endpoint: "https://login.salesforce.com/services/oauth2/token",
  refresh_endpoint: "https://login.salesforce.com/services/oauth2/token",
  client_id:
    "3MVG9gtDqcOkH4PIHJEX7YrYZrqFF1MLN6hTW_dnrQJGc6O23xHsDjXvSerZUMCZwcLxSwifcYUJ0F4Og.ouo",
  enforce_secrets: ["client_secret"],
};

const salesforceCrmIntegrationConfig: IntegrationConfig = {
  id: "salesforce_crm",
  name: "Salesforce",
  description: "Some description for Salesforce CRM",
  airbyte_id: "b117307c-14b6-41aa-9422-947e34922962",
  auth_strategies: [tokenOAuth2Strategy],
};

export default salesforceCrmIntegrationConfig;
