#!/usr/bin/env node
import * as cdk from "aws-cdk-lib";

import { EmployeeOpsInfrastructureStack } from "../lib/employee-ops-infrastructure-stack";

const app = new cdk.App();

new EmployeeOpsInfrastructureStack(app, "EmployeeOpsInfrastructureStack");

