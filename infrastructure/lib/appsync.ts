import { Stack, StackProps } from "aws-cdk-lib";
import {
  AuthorizationType,
  FieldLogLevel,
  GraphqlApi,
  MappingTemplate,
  Resolver,
  SchemaFile,
} from "aws-cdk-lib/aws-appsync";
import { RetentionDays } from "aws-cdk-lib/aws-logs";
import { Construct } from "constructs";
import * as path from "path";

export class AppsyncStack extends Stack {
  readonly gqlApi: GraphqlApi;

  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    this.gqlApi = new GraphqlApi(this, "appsync", {
      name: "mimo-appsync",
      schema: SchemaFile.fromAsset(
        path.join(__dirname, "graphql/schema.graphql")
      ),
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: AuthorizationType.OIDC,
          openIdConnectConfig: {
            oidcProvider: "https://dev-co2rq0sc2r5fv2gk.us.auth0.com/",
          },
        },
      },
      logConfig: {
        fieldLogLevel: FieldLogLevel.ALL,
        retention: RetentionDays.ONE_WEEK,
      },
      xrayEnabled: true,
    });

    // proxyMessage()
    new Resolver(this, "proxy-message-resolver", {
      api: this.gqlApi,
      typeName: "Mutation",
      fieldName: "proxyMessage",
      dataSource: this.gqlApi.addNoneDataSource("proxyMessageDS"),
      requestMappingTemplate: MappingTemplate.fromString(
        `{ "version" : "2018-05-29" }`
      ),
      responseMappingTemplate: MappingTemplate.fromString(
        "$util.toJson($context.arguments)"
      ),
    });

    // updatedMessage()
    new Resolver(this, "updated-message-resolver", {
      api: this.gqlApi,
      typeName: "Subscription",
      fieldName: "updatedMessage",
      dataSource: this.gqlApi.addNoneDataSource("updatedMessageDS"),
      requestMappingTemplate: MappingTemplate.fromString(
        `{ "version": "2018-05-29", "payload": $util.toJson($context.arguments) }`
      ),
      responseMappingTemplate: MappingTemplate.fromString(
        "$util.toJson($context.result)"
      ),
    });
  }
}
