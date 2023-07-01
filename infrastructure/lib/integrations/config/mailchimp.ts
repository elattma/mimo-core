import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://login.mailchimp.com/oauth2/authorize?response_type=code&client_id=110200010969",
  authorize_endpoint: "https://login.mailchimp.com/oauth2/token",
  refresh_endpoint: "https://login.mailchimp.com/oauth2/token",
  client_id: "110200010969",
  enforce_secrets: ["client_secret"],
};

const mailchimpIntegrationConfig: IntegrationConfig = {
  id: "mailchimp",
  name: "Mailchimp",
  description: "Some description for Mailchimp",
  airbyte_id: "b03a9f3e-22a5-11eb-adc1-0242ac120002",
  auth_strategies: [tokenOAuth2Strategy],
};

export default mailchimpIntegrationConfig;
