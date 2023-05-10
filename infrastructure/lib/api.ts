import { Stack, StackProps } from "aws-cdk-lib";
import {
  ApiKeySourceType,
  Authorizer,
  IResource,
  LambdaIntegration,
  Period,
  RestApi,
  TokenAuthorizer,
  UsagePlan,
} from "aws-cdk-lib/aws-apigateway";
import {
  Certificate,
  CertificateValidation,
} from "aws-cdk-lib/aws-certificatemanager";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { NodejsFunction } from "aws-cdk-lib/aws-lambda-nodejs";
import { HostedZone } from "aws-cdk-lib/aws-route53";
import { Secret } from "aws-cdk-lib/aws-secretsmanager";
import { Construct } from "constructs";
import {
  AuthorizerType,
  MimoUsagePlan,
  RouteConfig,
  UsageConfig,
} from "./model";
import path = require("path");

export interface ApiStackProps extends StackProps {
  readonly stageId: string;
  readonly domainName: string;
  readonly routeConfigs: RouteConfig[];
}

export class ApiStack extends Stack {
  readonly defaultUsagePlan: MimoUsagePlan;
  readonly api: RestApi;
  readonly authorizerMap: Map<AuthorizerType, Authorizer>;
  apiKeyLambda: NodejsFunction;

  constructor(scope: Construct, id: string, props: ApiStackProps) {
    super(scope, id, props);

    this.api = this.getRestApi(props.stageId, props.domainName);
    const appOAuthAuthorizer = this.getAppOAuthAuthorizer(
      this.api,
      props.stageId
    );
    const apiKeyAuthorizer = this.getApiKeyAuthorizer(this.api, props.stageId);
    this.authorizerMap = new Map<AuthorizerType, Authorizer>([
      [AuthorizerType.APP_OAUTH, appOAuthAuthorizer],
      [AuthorizerType.API_KEY, apiKeyAuthorizer],
    ]);

    const defaultUsageConfig: UsageConfig = {
      quotaLimit: 100,
      quotaPeriod: Period.DAY,
      throttleRateLimit: 10,
      throttleBurstLimit: 2,
    };
    const defaultPlanName = "default";
    const usagePlan = this.getUsagePlan(
      this.api,
      defaultPlanName,
      props.stageId,
      defaultUsageConfig
    );
    this.defaultUsagePlan = {
      name: defaultPlanName,
      config: defaultUsageConfig,
      plan: usagePlan,
    };

    for (const routeConfig of props.routeConfigs) {
      this.getRoute(this.api, this.api.root, routeConfig);
    }
  }

  getRestApi = (stageId: string, tld: string): RestApi => {
    const zone = HostedZone.fromLookup(this, "hosted-zone", {
      domainName: tld,
    });

    let domainName = "";
    if (stageId !== "beta") {
      domainName = `${stageId}.${tld}`;
    } else {
      domainName = `api.${tld}`;
    }
    const api = new RestApi(this, `${stageId}-mimo-api`, {
      domainName: {
        domainName: domainName,
        certificate: new Certificate(this, `${stageId}-api-cert`, {
          domainName: domainName,
          validation: CertificateValidation.fromDns(zone),
        }),
      },
      defaultCorsPreflightOptions: {
        allowHeaders: [
          "Content-Type",
          "X-Amz-Date",
          "Authorization",
          "X-Api-Key",
          "X-Amz-Security-Token",
        ],
        statusCode: 200,
        allowMethods: ["OPTIONS", "GET", "POST", "DELETE"],
        allowCredentials: true,
        allowOrigins: ["https://www.mimo.team"],
      },
      apiKeySourceType: ApiKeySourceType.HEADER,
    });

    return api;
  };

  getAppOAuthAuthorizer = (api: RestApi, stage: string): Authorizer => {
    const auth0SecretName = "beta/Mimo/Integrations/Auth0";
    const auth0Secret = Secret.fromSecretNameV2(
      this,
      "auth0-secret",
      auth0SecretName
    );
    const authorizerLambda = new NodejsFunction(
      this,
      "app-oauth-authorizer-lambda",
      {
        runtime: Runtime.NODEJS_18_X,
        handler: "handler",
        entry: path.join(__dirname, "authorizers/app_oauth.ts"),
        environment: {
          STAGE: "beta",
        },
      }
    );
    const authorizer = new TokenAuthorizer(this, "app-oauth-token-authorizer", {
      handler: authorizerLambda,
      authorizerName: "oauth_token",
    });
    auth0Secret.grantRead(authorizerLambda);
    authorizer._attachToApi(api);
    return authorizer;
  };

  getApiKeyAuthorizer = (api: RestApi, stage: string): Authorizer => {
    const authorizerLambda = new NodejsFunction(
      this,
      "api-key-authorizer-lambda",
      {
        runtime: Runtime.NODEJS_18_X,
        handler: "handler",
        entry: path.join(__dirname, "authorizers/api_key.ts"),
        environment: {
          TABLE_NAME: `mimo-${stage}-pc`,
          DEVELOPER_SECRET_PATH_PREFIX: `/${stage}/developer`,
        },
      }
    );
    this.apiKeyLambda = authorizerLambda;
    const authorizer = new TokenAuthorizer(this, "api-key-token-authorizer", {
      handler: authorizerLambda,
      authorizerName: "api_key",
    });
    authorizer._attachToApi(api);
    return authorizer;
  };

  getUsagePlan = (
    api: RestApi,
    name: string,
    stage: string,
    usageConfig: UsageConfig
  ): UsagePlan => {
    return api.addUsagePlan(`${stage}-${name}-usage-plan`, {
      name: `${stage}-${name}-usage-plan`,
      throttle: {
        rateLimit: usageConfig.throttleRateLimit,
        burstLimit: usageConfig.throttleBurstLimit,
      },
      quota: {
        limit: usageConfig.quotaLimit,
        period: usageConfig.quotaPeriod,
      },
      apiStages: [
        {
          api: api,
          stage: api.deploymentStage,
        },
      ],
    });
  };

  getRoute = (api: RestApi, resource: IResource, routeConfig: RouteConfig) => {
    const route = resource.addResource(routeConfig.path);
    let idRoute = undefined;
    if (routeConfig.idResource) {
      idRoute = route.addResource(`{${routeConfig.idResource}}`);
    }
    if (routeConfig.subRoutes) {
      for (const subRoute of routeConfig.subRoutes) {
        this.getRoute(api, route, subRoute);
      }
    }
    if (!routeConfig.methods) {
      return;
    }
    const requestValidator = api.addRequestValidator(
      `${routeConfig.path}-request-validator`,
      {
        validateRequestBody: true,
        validateRequestParameters: true,
      }
    );
    for (const method of routeConfig.methods) {
      const requestModel = method.requestModelOptions
        ? api.addModel(
            `${routeConfig.path}-${method.name}-request-model`,
            method.requestModelOptions
          )
        : undefined;

      const requestParameters = method.requestParameters
        ? method.requestParameters
        : {};
      if (method.idResource) {
        requestParameters[`method.request.path.${method.idResource}`] = false;
      }

      const responseModel = api.addModel(
        `${routeConfig.path}-${method.name}-response-model`,
        method.responseModelOptions
      );

      let authorizer: Authorizer | undefined = this.authorizerMap.get(
        method.authorizerType
      );

      route.addMethod(method.name, new LambdaIntegration(method.handler), {
        authorizer: authorizer,
        apiKeyRequired: method.apiKeyRequired,
        requestValidator: requestValidator,
        requestModels: requestModel
          ? {
              "application/json": requestModel,
            }
          : undefined,
        requestParameters: requestParameters,
        methodResponses: [
          {
            statusCode: "200",
            responseModels: {
              "application/json": responseModel,
            },
            responseParameters: {
              "method.response.header.Content-Type": true,
              "method.response.header.Access-Control-Allow-Origin": true,
              "method.response.header.Access-Control-Allow-Credentials": true,
            },
          },
        ],
      });

      if (method.idResource && idRoute) {
        idRoute.addMethod(method.name, new LambdaIntegration(method.handler), {
          authorizer: authorizer,
          apiKeyRequired: method.apiKeyRequired,
          requestValidator: requestValidator,
          requestModels: requestModel
            ? {
                "application/json": requestModel,
              }
            : undefined,
          requestParameters: requestParameters,
          methodResponses: [
            {
              statusCode: "200",
              responseModels: {
                "application/json": responseModel,
              },
              responseParameters: {
                "method.response.header.Content-Type": true,
                "method.response.header.Access-Control-Allow-Origin": true,
                "method.response.header.Access-Control-Allow-Credentials": true,
              },
            },
          ],
        });
      }
    }
  };
}
