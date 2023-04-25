import { PythonFunction } from "@aws-cdk/aws-lambda-python-alpha";
import { ModelOptions, Period, UsagePlan } from "aws-cdk-lib/aws-apigateway";

export interface MethodConfig {
  name: string;
  handler: PythonFunction;
  requestModelOptions?: ModelOptions;
  requestParameters?: {
    [param: string]: boolean;
  };
  responseModelOptions: ModelOptions;
}

export interface RouteConfig {
  path: string;
  methods: MethodConfig[];
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
