import {
  PythonFunction,
  PythonLayerVersion,
} from "@aws-cdk/aws-lambda-python-alpha";
import { Duration, Stack, StackProps } from "aws-cdk-lib";
import { JsonSchemaType, ModelOptions } from "aws-cdk-lib/aws-apigateway";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import { MethodConfig } from "../../model";
import path = require("path");

export interface LocksmithStackProps extends StackProps {
  readonly stageId: string;
  readonly layers?: Map<string, PythonLayerVersion>;
}

export class LocksmithStack extends Stack {
  readonly methods: MethodConfig[] = [];

  constructor(scope: Construct, id: string, props: LocksmithStackProps) {
    super(scope, id, props);

    const layers: PythonLayerVersion[] = [];
    const generateMethod = this.getGenerateMethod(props.stageId, layers);
    this.methods.push(generateMethod);
    const getMethod = this.getGetMethod(props.stageId, layers);
    this.methods.push(getMethod);
    const deleteMethod = this.getDeleteMethod(props.stageId, layers);
    this.methods.push(deleteMethod);
  }

  getGenerateMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-locksmith-generate-lambda`,
      {
        entry: path.join(__dirname, "assets"),
        index: "generate.py",
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        timeout: Duration.seconds(30),
        memorySize: 1024,
        environment: {
          STAGE: stage,
        },
        retryAttempts: 0,
        bundling: {
          assetExcludes: ["**.venv**", "**__pycache__**"],
        },
        layers: layers,
      }
    );

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "LocksmithGenerateResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          apiKey: {
            type: JsonSchemaType.OBJECT,
            properties: {
              value: {
                type: JsonSchemaType.STRING,
              },
            },
          },
        },
      },
    };

    return {
      name: "POST",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };

  getGetMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(this, `${stage}-locksmith-get-lambda`, {
      entry: path.join(__dirname, "assets"),
      index: "get.py",
      runtime: Runtime.PYTHON_3_9,
      handler: "handler",
      timeout: Duration.seconds(30),
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
      modelName: "LocksmithGetResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          apiKey: {
            type: JsonSchemaType.OBJECT,
            properties: {
              value: {
                type: JsonSchemaType.STRING,
              },
            },
          },
        },
      },
    };

    return {
      name: "GET",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };

  getDeleteMethod = (
    stage: string,
    layers: PythonLayerVersion[]
  ): MethodConfig => {
    const handler = new PythonFunction(
      this,
      `${stage}-locksmith-delete-lambda`,
      {
        entry: path.join(__dirname, "assets"),
        index: "delete.py",
        runtime: Runtime.PYTHON_3_9,
        handler: "handler",
        timeout: Duration.seconds(30),
        memorySize: 1024,
        environment: {
          STAGE: stage,
        },
        retryAttempts: 0,
        bundling: {
          assetExcludes: ["**.venv**", "**__pycache__**"],
        },
        layers: layers,
      }
    );

    const methodResponseOptions: ModelOptions = {
      contentType: "application/json",
      modelName: "LocksmithDeleteResponse",
      schema: {
        type: JsonSchemaType.OBJECT,
        properties: {
          success: {
            type: JsonSchemaType.BOOLEAN,
            default: true,
          },
        },
      },
    };

    return {
      name: "DELETE",
      handler: handler,
      responseModelOptions: methodResponseOptions,
      use_authorizer: true,
    };
  };
}
