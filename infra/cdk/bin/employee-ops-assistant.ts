#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";

import { parseApplicationConfig } from "../lib/application-config";
import { EmployeeOpsInfrastructureStack } from "../lib/employee-ops-infrastructure-stack";

const app = new cdk.App();

const agentApiSecretName = app.node.tryGetContext("agentApiSecretName");
const applicationConfig = parseApplicationConfig(
  app.node.tryGetContext("applicationConfig"),
);
const githubActionsBranch = app.node.tryGetContext("githubActionsBranch");
const githubActionsRepository = app.node.tryGetContext(
  "githubActionsRepository",
);
const instanceType = app.node.tryGetContext("instanceType");
const keyPairName = app.node.tryGetContext("keyPairName");
const oauth2ProxySecretName = app.node.tryGetContext("oauth2ProxySecretName");
const rootVolumeSizeGiB = app.node.tryGetContext("rootVolumeSizeGiB");
const targetAccount = app.node.tryGetContext("targetAccount");
const targetRegion = app.node.tryGetContext("targetRegion");
const sshAllowedCidr = app.node.tryGetContext("sshAllowedCidr");

if (
  typeof agentApiSecretName !== "string" ||
  agentApiSecretName.length === 0
) {
  throw new Error("CDK context agentApiSecretName must be a non-empty string.");
}

if (typeof instanceType !== "string" || instanceType.length === 0) {
  throw new Error("CDK context instanceType must be a non-empty string.");
}

if (
  typeof githubActionsBranch !== "string" ||
  githubActionsBranch.length === 0
) {
  throw new Error(
    "CDK context githubActionsBranch must be a non-empty string.",
  );
}

if (
  typeof githubActionsRepository !== "string" ||
  githubActionsRepository.length === 0
) {
  throw new Error(
    "CDK context githubActionsRepository must be a non-empty string.",
  );
}

if (typeof keyPairName !== "string" || keyPairName.length === 0) {
  throw new Error("CDK context keyPairName must be a non-empty string.");
}

if (
  typeof oauth2ProxySecretName !== "string" ||
  oauth2ProxySecretName.length === 0
) {
  throw new Error(
    "CDK context oauth2ProxySecretName must be a non-empty string.",
  );
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
  agentApiSecretName,
  applicationConfig,
  description: "AWS infrastructure for Employee Ops Assistant",
  env: {
    account: targetAccount,
    region: targetRegion,
  },
  githubActionsBranch,
  githubActionsRepository,
  instanceType,
  keyPairName,
  oauth2ProxySecretName,
  rootVolumeSizeGiB,
  sshAllowedCidr,
});
