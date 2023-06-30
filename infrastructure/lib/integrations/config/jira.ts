import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://auth.atlassian.com/authorize?audience=api.atlassian.com&client_id=iBLxYA68uF88tqfp11R2pKuJWKsg10BY&scope=read%3Ajira-work%20read%3Ajira-user&response_type=code&prompt=consent",
  authorize_endpoint: "https://auth.atlassian.com/oauth/token",
  refresh_endpoint: "https://auth.atlassian.com/oauth/token",
  client_id: "iBLxYA68uF88tqfp11R2pKuJWKsg10BY",
  enforce_secrets: ["client_secret"],
};

const jiraIntegrationConfig: IntegrationConfig = {
  id: "jira",
  name: "Jira",
  description: "Some description for Jira",
  auth_strategies: [tokenOAuth2Strategy],
};

export default jiraIntegrationConfig;
