import { PythonLayerVersion } from "@aws-cdk/aws-lambda-python-alpha";
import { Stack, StackProps } from "aws-cdk-lib";
import { Runtime } from "aws-cdk-lib/aws-lambda";
import { Construct } from "constructs";
import path = require("path");

export interface LayerStackProps extends StackProps {
  readonly stageId: string;
}

export class LayerStack extends Stack {
  readonly layers: Map<string, PythonLayerVersion> = new Map();

  constructor(scope: Construct, id: string, props: LayerStackProps) {
    super(scope, id, props);

    const LAYERS = ["aws", "external", "fetcher", "graph", "mystery"];
    LAYERS.forEach((layerName) => {
      const layer = this.getLayer(props.stageId, layerName);
      this.layers.set(layerName, layer);
    });
  }

  getLayer = (stageId: string, name: string): PythonLayerVersion => {
    const layer = new PythonLayerVersion(this, `${stageId}-${name}-layer`, {
      entry: path.join(__dirname, `layers/${name}`),
      bundling: {
        assetExcludes: ["**.venv**", "**pycache**"],
      },
      compatibleRuntimes: [Runtime.PYTHON_3_9],
    });

    return layer;
  };
}
