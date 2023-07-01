import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://oauth.pipedrive.com/oauth/authorize?client_id=5100b7bc6320cf25",
  authorize_endpoint: "https://oauth.pipedrive.com/oauth/token",
  refresh_endpoint: "https://oauth.pipedrive.com/oauth/token",
  client_id: "5100b7bc6320cf25",
  enforce_secrets: ["client_secret"],
};

const pipedriveIntegrationConfig: IntegrationConfig = {
  id: "pipedrive",
  name: "Pipedrive",
  description: "Some description for Pipedrive",
  auth_strategies: [tokenOAuth2Strategy],
};

export default pipedriveIntegrationConfig;
