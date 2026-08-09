import { ArnFormat, Duration, Stack } from "aws-cdk-lib";
import { CfnOIDCProvider } from "aws-cdk-lib/aws-iam";
import {
  Effect,
  FederatedPrincipal,
  PolicyStatement,
  Role,
  type IRole,
} from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";

import type { ApplicationRepositories } from "./application-repositories";

const GITHUB_OIDC_ISSUER = "https://token.actions.githubusercontent.com";
const GITHUB_OIDC_AUDIENCE = "sts.amazonaws.com";

export const DEPLOYMENT_TARGET_TAG_KEY = "EmployeeOpsDeploymentTarget";
export const DEPLOYMENT_TARGET_TAG_VALUE = "true";

export interface GitHubEcrPublisherProps {
  readonly branch: string;
  readonly repositories: ApplicationRepositories;
  readonly repository: string;
}

export function createGitHubEcrPublisherRole(
  scope: Construct,
  props: GitHubEcrPublisherProps,
): IRole {
  const provider = new CfnOIDCProvider(scope, "GitHubOidcProvider", {
    clientIdList: [GITHUB_OIDC_AUDIENCE],
    url: GITHUB_OIDC_ISSUER,
  });

  const role = new Role(scope, "GitHubEcrPublisherRole", {
    assumedBy: new FederatedPrincipal(
      provider.attrArn,
      {
        StringEquals: {
          "token.actions.githubusercontent.com:aud": GITHUB_OIDC_AUDIENCE,
          "token.actions.githubusercontent.com:sub":
            `repo:${props.repository}:ref:refs/heads/${props.branch}`,
        },
      },
      "sts:AssumeRoleWithWebIdentity",
    ),
    description:
      "Publishes and deploys Employee Ops Assistant images from GitHub Actions",
    maxSessionDuration: Duration.hours(1),
    roleName: "employee-ops-github-ecr-publisher",
  });

  role.addToPrincipalPolicy(
    new PolicyStatement({
      actions: ["ecr:GetAuthorizationToken"],
      effect: Effect.ALLOW,
      resources: ["*"],
    }),
  );
  role.addToPrincipalPolicy(
    new PolicyStatement({
      actions: [
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeImages",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
      ],
      effect: Effect.ALLOW,
      resources: Object.values(props.repositories).map(
        (repository) => repository.repositoryArn,
      ),
    }),
  );

  return role;
}

export function grantGitHubSsmDeploymentAccess(
  scope: Construct,
  role: IRole,
): void {
  const stack = Stack.of(scope);
  const runShellScriptDocumentArn = stack.formatArn({
    account: "",
    arnFormat: ArnFormat.SLASH_RESOURCE_NAME,
    resource: "document",
    resourceName: "AWS-RunShellScript",
    service: "ssm",
  });
  const deploymentTargetArn = stack.formatArn({
    arnFormat: ArnFormat.SLASH_RESOURCE_NAME,
    resource: "instance",
    resourceName: "*",
    service: "ec2",
  });

  role.addToPrincipalPolicy(
    new PolicyStatement({
      actions: ["ssm:SendCommand"],
      effect: Effect.ALLOW,
      resources: [runShellScriptDocumentArn],
    }),
  );
  role.addToPrincipalPolicy(
    new PolicyStatement({
      actions: ["ssm:SendCommand"],
      conditions: {
        StringEquals: {
          [`ssm:resourceTag/${DEPLOYMENT_TARGET_TAG_KEY}`]:
            DEPLOYMENT_TARGET_TAG_VALUE,
        },
      },
      effect: Effect.ALLOW,
      resources: [deploymentTargetArn],
    }),
  );
  role.addToPrincipalPolicy(
    new PolicyStatement({
      actions: ["ssm:ListCommandInvocations"],
      effect: Effect.ALLOW,
      resources: ["*"],
    }),
  );
}
