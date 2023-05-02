import {
  AuthType,
  IntegrationConfig,
  TokenDirectAuthStrategy,
  TokenOAuth2AuthStrategy,
} from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.coql.READ&client_id=1000.FOXW2IM5QG3WT0PJTJZDW6WJKQ9LEQ&response_type=code&access_type=offline&prompt=consent",
  authorize_endpoint: "https://accounts.zoho.com/oauth/v2/token",
  refresh_endpoint: "https://accounts.zoho.com/oauth/v2/token",
  client_id: "1000.FOXW2IM5QG3WT0PJTJZDW6WJKQ9LEQ",
  enforce_secrets: ["client_secret"],
};

const tokenDirectStrategy: TokenDirectAuthStrategy = {
  type: AuthType.TOKEN_DIRECT,
};

const zohoCrmIntegrationConfig: IntegrationConfig = {
  id: "zoho_crm",
  name: "Zoho CRM",
  description: "Some description for Zoho CRM",
  auth_strategies: [tokenOAuth2Strategy, tokenDirectStrategy],
};

export default zohoCrmIntegrationConfig;
