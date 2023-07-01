import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://auth.monday.com/oauth2/authorize?client_id=9a2f22031c207f56ed6c542d36862328",
  authorize_endpoint: "https://auth.monday.com/oauth2/token",
  refresh_endpoint: "https://auth.monday.com/oauth2/token",
  client_id: "9a2f22031c207f56ed6c542d36862328",
  enforce_secrets: ["client_secret"],
};

const mondayIntegrationConfig: IntegrationConfig = {
  id: "monday",
  name: "Monday",
  description: "Some description for Monday",
  airbyte_id: "80a54ea2-9959-4040-aac1-eee42423ec9b",
  auth_strategies: [tokenOAuth2Strategy],
};

export default mondayIntegrationConfig;
