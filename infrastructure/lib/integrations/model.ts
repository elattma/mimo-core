export type IntegrationId = string;

export enum AuthType {
  TOKEN_OAUTH2 = "token_oauth2",
  TOKEN_DIRECT = "token_direct",
}

export interface AuthStrategy {
  type: AuthType;
}

export interface TokenOAuth2AuthStrategy extends AuthStrategy {
  type: AuthType.TOKEN_OAUTH2;
  oauth2_link: string;
  authorize_endpoint: string;
  client_id: string;
  enforce_secrets: string[];
  refresh_endpoint?: string;
}

export interface TokenDirectAuthStrategy extends AuthStrategy {
  type: AuthType.TOKEN_DIRECT;
}

export interface IntegrationConfig {
  id: IntegrationId;
  name: string;
  description: string;
  airbyte_id?: string;
  auth_strategies: AuthStrategy[];
}
