import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { ModelOptions, Period, UsagePlan } from "aws-cdk-lib/aws-apigateway";

export enum AuthorizerType {
  APP_OAUTH = "APP_OAUTH",
  API_KEY = "API_KEY",
}

export interface MethodConfig {
  name: string;
  handler: PythonFunction;
  responseModelOptions: ModelOptions;
  authorizerType: AuthorizerType;
  requestModelOptions?: ModelOptions;
  idResource?: string;
  requestParameters?: {
    [param: string]: boolean;
  };
}

export interface RouteConfig {
  path: string;
  methods: MethodConfig[];
  subRoutes?: RouteConfig[];
  idResource?: string;
}

export interface UsageConfig {
  quotaLimit: number;
  quotaPeriod: Period;
  throttleRateLimit: number;
  throttleBurstLimit: number;
}

export interface MimoUsagePlan {
  name: string;
  config: UsageConfig;
  plan: UsagePlan;
}
