#!/usr/bin/env node
import { App } from "aws-cdk-lib";
import { MimoStage } from "../lib/stage";

const app = new App();
new MimoStage(app, "mimo-beta", {
  env: {
    account: "222250063412",
    region: "us-east-1",
  },
  domainName: "mimo.team",
  stageId: "beta",
});
