import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://linear.app/oauth/authorize?client_id=0c043f66475b304f146ace3ada0e04e5&response_type=code&scope=read&prompt=consent",
  authorize_endpoint: "https://api.linear.app/oauth/token",
  refresh_endpoint: "https://api.linear.app/oauth/token",
  client_id: "0c043f66475b304f146ace3ada0e04e5",
  enforce_secrets: ["client_secret"],
};

const linearIntegrationConfig: IntegrationConfig = {
  id: "linear",
  name: "Linear",
  description: "Some description for Linear",
  auth_strategies: [tokenOAuth2Strategy],
};

export default linearIntegrationConfig;
