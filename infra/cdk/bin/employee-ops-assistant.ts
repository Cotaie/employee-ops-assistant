#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";

import { EmployeeOpsInfrastructureStack } from "../lib/employee-ops-infrastructure-stack";

const app = new cdk.App();

const targetAccount = app.node.tryGetContext("targetAccount");
const targetRegion = app.node.tryGetContext("targetRegion");

if (typeof targetAccount !== "string" || targetAccount.length === 0) {
  throw new Error("CDK context targetAccount must be a non-empty string.");
}

if (typeof targetRegion !== "string" || targetRegion.length === 0) {
  throw new Error("CDK context targetRegion must be a non-empty string.");
}

new EmployeeOpsInfrastructureStack(app, "EmployeeOpsInfrastructureStack", {
  description: "AWS infrastructure for Employee Ops Assistant",
  env: {
    account: targetAccount,
    region: targetRegion,
  },
});
