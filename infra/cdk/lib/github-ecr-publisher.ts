import { Duration } from "aws-cdk-lib";
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
    description: "Publishes Employee Ops Assistant images from GitHub Actions",
    maxSessionDuration: Duration.hours(1),
    roleName: "employee-ops-github-ecr-publisher",
  });

  role.addToPolicy(
    new PolicyStatement({
      actions: ["ecr:GetAuthorizationToken"],
      effect: Effect.ALLOW,
      resources: ["*"],
    }),
  );
  role.addToPolicy(
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
