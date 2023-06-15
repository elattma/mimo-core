import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://slack.com/oauth/v2/authorize?scope=groups:history&client_id=3857399127559.4690380022609",
  authorize_endpoint: "https://slack.com/api/oauth.v2.access",
  client_id: "3857399127559.4690380022609",
  enforce_secrets: ["client_secret"],
};

const slackMessagingIntegrationConfig: IntegrationConfig = {
  id: "slack_messaging",
  name: "Slack",
  description: "Some description for Slack",
  airbyte_id: "c2281cee-86f9-4a86-bb48-d23286b4c7bd",
  auth_strategies: [tokenOAuth2Strategy],
};

export default slackMessagingIntegrationConfig;
