import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://api.notion.com/v1/oauth/authorize?client_id=c23b0a26-4048-4fe6-888b-f6a89ce1caac&response_type=code&owner=user",
  authorize_endpoint: "https://api.notion.com/v1/oauth/token",
  refresh_endpoint: "https://api.notion.com/v1/oauth/token",
  client_id: "c23b0a26-4048-4fe6-888b-f6a89ce1caac",
  enforce_secrets: ["client_secret"],
};

const notionDocsIntegrationConfig: IntegrationConfig = {
  id: "notion_docs",
  name: "Notion",
  description: "Some description for Notion Docs",
  airbyte_id: "6e00b415-b02e-4160-bf02-58176a0ae687",
  auth_strategies: [tokenOAuth2Strategy],
};

export default notionDocsIntegrationConfig;
