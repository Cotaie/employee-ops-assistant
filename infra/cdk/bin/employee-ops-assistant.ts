#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";

import { EmployeeOpsInfrastructureStack } from "../lib/employee-ops-infrastructure-stack";

const app = new cdk.App();

const instanceType = app.node.tryGetContext("instanceType");
const keyPairName = app.node.tryGetContext("keyPairName");
const rootVolumeSizeGiB = app.node.tryGetContext("rootVolumeSizeGiB");
const targetAccount = app.node.tryGetContext("targetAccount");
const targetRegion = app.node.tryGetContext("targetRegion");
const sshAllowedCidr = app.node.tryGetContext("sshAllowedCidr");

if (typeof instanceType !== "string" || instanceType.length === 0) {
  throw new Error("CDK context instanceType must be a non-empty string.");
}

if (typeof keyPairName !== "string" || keyPairName.length === 0) {
  throw new Error("CDK context keyPairName must be a non-empty string.");
}

if (
  typeof rootVolumeSizeGiB !== "number" ||
  !Number.isInteger(rootVolumeSizeGiB) ||
  rootVolumeSizeGiB <= 0
) {
  throw new Error("CDK context rootVolumeSizeGiB must be a positive integer.");
}

if (typeof targetAccount !== "string" || targetAccount.length === 0) {
  throw new Error("CDK context targetAccount must be a non-empty string.");
}

if (typeof targetRegion !== "string" || targetRegion.length === 0) {
  throw new Error("CDK context targetRegion must be a non-empty string.");
}

if (typeof sshAllowedCidr !== "string" || sshAllowedCidr.length === 0) {
  throw new Error("CDK context sshAllowedCidr must be a non-empty string.");
}

new EmployeeOpsInfrastructureStack(app, "EmployeeOpsInfrastructureStack", {
  description: "AWS infrastructure for Employee Ops Assistant",
  env: {
    account: targetAccount,
    region: targetRegion,
  },
  instanceType,
  keyPairName,
  rootVolumeSizeGiB,
  sshAllowedCidr,
});
