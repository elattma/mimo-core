import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { ModelOptions, Period, UsagePlan } from "aws-cdk-lib/aws-apigateway";

export interface MethodConfig {
  name: string;
  handler: PythonFunction;
  responseModelOptions: ModelOptions;
  use_authorizer?: boolean;
  api_key_required?: boolean;
  requestModelOptions?: ModelOptions;
  requestParameters?: {
    [param: string]: boolean;
  };
}

export interface RouteConfig {
  path: string;
  methods: MethodConfig[];
  subRoutes?: RouteConfig[];
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
