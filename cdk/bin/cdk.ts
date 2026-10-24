#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { AgentStack } from "../lib/agent-stack";

const app = new cdk.App();
new AgentStack(app, "AgentStack", {
  env: {
    region: "us-east-1",
  },
});
