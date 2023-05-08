import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { AuthorizerType, MethodConfig } from "../../model";
import path = require("path");

export interface UsageMonitorStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class UsageMonitorStack extends Stack {
  readonly methods: MethodConfig[] = [];

  constructor(scope: Construct, id: string, props: UsageMonitorStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
    const usageMethod = this.getUsageMethod(props.stageId, layers);
    this.methods.push(usageMethod);
  }

  getUsageMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-usage-lambda`, {
      entry: path.join(__dirname, "assets"),
      index: "usage.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.minutes(15),
      memorySize: 1024,
      environment: {
        STAGE: stage,
      },
      retryAttempts: 0,
      bundling: {
        assetExcludes: ["**.venv**", "**__pycache__**"],
      },
      layers: layers,
    });

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "UsageGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          usage: {
            type: JsonSchemaType.OBJECT,
            properties: {
              used: {
                type: JsonSchemaType.INTEGER,
              },
              remaining: {
                type: JsonSchemaType.INTEGER,
              },
            },
          },
        },
        required: ["usage"],
      },
    };

    return {
      name: "GET",
      handler: handler,
      authorizerType: AuthorizerType.APP_OAUTH,
      responseModelOptions: methodResponseOptions,
    };
  };
}
