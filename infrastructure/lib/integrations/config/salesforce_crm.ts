import {
  AuthType,
  IntegrationConfig,
  TokenDirectAuthStrategy,
  TokenOAuth2AuthStrategy,
} from "../model";

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

const tokenDirectStrategy: TokenDirectAuthStrategy = {
  type: AuthType.TOKEN_DIRECT,
};

const salesforceCrmIntegrationConfig: IntegrationConfig = {
  id: "salesforce_crm",
  name: "Salesforce CRM",
  description: "Some description for Salesforce CRM",
  auth_strategies: [tokenOAuth2Strategy, tokenDirectStrategy],
};

export default salesforceCrmIntegrationConfig;
