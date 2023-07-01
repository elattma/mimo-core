import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://app.clickup.com/api?client_id=TMHA3AJPE9RR9ZI5DIZ8ZRN7JU68KS2P",
  authorize_endpoint: "https://api.clickup.com/api/v2/oauth/token",
  refresh_endpoint: "https://api.clickup.com/api/v2/oauth/token",
  client_id: "TMHA3AJPE9RR9ZI5DIZ8ZRN7JU68KS2P",
  enforce_secrets: ["client_secret"],
};

const clickupIntegrationConfig: IntegrationConfig = {
  id: "clickup",
  name: "ClickUp",
  description: "Some description for ClickUp",
  auth_strategies: [tokenOAuth2Strategy],
};

export default clickupIntegrationConfig;
