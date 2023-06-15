import { AuthType, IntegrationConfig, TokenOAuth2AuthStrategy } from "../model";

const tokenOAuth2Strategy: TokenOAuth2AuthStrategy = {
  type: AuthType.TOKEN_OAUTH2,
  oauth2_link:
    "https://accounts.google.com/o/oauth2/v2/auth?client_id=195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com&scope=https://www.googleapis.com/auth/drive.readonly&response_type=code&access_type=offline&prompt=consent",
  authorize_endpoint: "https://oauth2.googleapis.com/token",
  refresh_endpoint: "https://oauth2.googleapis.com/token",
  client_id:
    "195189627384-2s7kncngrga0adasklb34d6v5hm8c1nu.apps.googleusercontent.com",
  enforce_secrets: ["client_secret"],
};

const googleDocsIntegrationConfig: IntegrationConfig = {
  id: "google_docs",
  name: "Google Docs",
  description: "Some description for Google Docs",
  auth_strategies: [tokenOAuth2Strategy],
};

export default googleDocsIntegrationConfig;
