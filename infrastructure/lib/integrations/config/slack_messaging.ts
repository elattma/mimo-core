import {
  AuthType,
  IntegrationConfig,
  TokenDirectAuthStrategy,
  TokenOAuth2AuthStrategy,
} from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://slack.com/oauth/v2/authorize?scope=groups:history&client_id=3857399127559.4690380022609",
  authorize_endpoint: "https://slack.com/api/oauth.v2.access",
  client_id: "3857399127559.4690380022609",
  enforce_secrets: ["client_secret"],
};

const tokenDirectStrategy: TokenDirectAuthStrategy = {
  type: AuthType.TOKEN_DIRECT,
};

const slackMessagingIntegrationConfig: IntegrationConfig = {
  id: "slack_messaging",
  name: "Slack",
  description: "Some description for Slack",
  auth_strategies: [tokenOAuth2Strategy, tokenDirectStrategy],
};

export default slackMessagingIntegrationConfig;
