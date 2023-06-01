import {
  AuthType,
  IntegrationConfig,
  TokenDirectAuthStrategy,
  TokenOAuth2AuthStrategy,
} from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://app.intercom.com/oauth?client_id=6e5f6e33-a5d5-4170-be21-0ca9713cae6e",
  authorize_endpoint: "https://api.intercom.io/auth/eagle/token",
  refresh_endpoint: "https://api.intercom.io/auth/eagle/token",
  client_id: "6e5f6e33-a5d5-4170-be21-0ca9713cae6e",
  enforce_secrets: ["client_secret"],
};

const tokenDirectStrategy: TokenDirectAuthStrategy = {
  type: AuthType.TOKEN_DIRECT,
};

const intercomSupportIntegrationConfig: IntegrationConfig = {
  id: "intercom_support",
  name: "Intercom Customer Support",
  description: "Some description for Intercom Support",
  airbyte_id: "d8313939-3782-41b0-be29-b3ca20d8dd3a",
  auth_strategies: [tokenOAuth2Strategy, tokenDirectStrategy],
};

export default intercomSupportIntegrationConfig;
