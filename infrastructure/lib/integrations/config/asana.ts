import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://app.asana.com/-/oauth_authorize?client_id=1204946351977507&response_type=code&scope=default",
  authorize_endpoint: "https://app.asana.com/-/oauth_token",
  refresh_endpoint: "https://app.asana.com/-/oauth_token",
  client_id: "1204946351977507",
  enforce_secrets: ["client_secret"],
};

const asanaIntegrationConfig: IntegrationConfig = {
  id: "asana",
  name: "Asana",
  description: "Some description for Asana",
  airbyte_id: "d0243522-dccf-4978-8ba0-37ed47a0bdbf",
  auth_strategies: [tokenOAuth2Strategy],
};

export default asanaIntegrationConfig;
