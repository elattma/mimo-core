import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=34742503-198c-4e12-a2e1-2951fa081e72&scope=offline_access%20user.read%20mail.read&response_type=code&response_mode=query",
  authorize_endpoint:
    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
  refresh_endpoint:
    "https://login.microsoftonline.com/common/oauth2/v2.0/token",
  client_id: "34742503-198c-4e12-a2e1-2951fa081e72",
  enforce_secrets: ["client_secret"],
};

const microsoftMailIntegrationConfig: IntegrationConfig = {
  id: "microsoft_mail",
  name: "Outlook",
  description: "Some description for Microsoft Mail",
  auth_strategies: [tokenOAuth2Strategy],
};

export default microsoftMailIntegrationConfig;
