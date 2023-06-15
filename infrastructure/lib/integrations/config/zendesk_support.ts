import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://d3v-mimo3158.zendesk.com/oauth/authorizations/new?response_type=code&client_id=zdg-mimo",
  authorize_endpoint: "https://d3v-mimo3158.zendesk.com/oauth/tokens",
  refresh_endpoint: "https://d3v-mimo3158.zendesk.com/oauth/tokens",
  client_id: "zdg-mimo",
  enforce_secrets: ["client_secret"],
};

const zendeskSupportIntegrationConfig: IntegrationConfig = {
  id: "zendesk_support",
  name: "Zendesk Customer Support",
  description: "Some description for Zendesk Customer Support",
  airbyte_id: "79c1aa37-dae3-42ae-b333-d1c105477715",
  auth_strategies: [tokenOAuth2Strategy],
};

export default zendeskSupportIntegrationConfig;
