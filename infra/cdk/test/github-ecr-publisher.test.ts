import { App, Stack } from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import test from "node:test";

import { createApplicationRepositories } from "../lib/application-repositories";
import {
  createGitHubEcrPublisherRole,
  grantGitHubSsmDeploymentAccess,
} from "../lib/github-ecr-publisher";

test("restricts GitHub image publishing to main and application repositories", () => {
  const app = new App();
  const stack = new Stack(app, "TestStack");
  const repositories = createApplicationRepositories(stack);

  createGitHubEcrPublisherRole(stack, {
    branch: "main",
    repositories,
    repository: "Cotaie/employee-ops-assistant",
  });

  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::IAM::OIDCProvider", {
    ClientIdList: ["sts.amazonaws.com"],
    Url: "https://token.actions.githubusercontent.com",
  });
  template.hasResourceProperties("AWS::IAM::Role", {
    AssumeRolePolicyDocument: {
      Statement: [
        Match.objectLike({
          Action: "sts:AssumeRoleWithWebIdentity",
          Condition: {
            StringEquals: {
              "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
              "token.actions.githubusercontent.com:sub":
                "repo:Cotaie/employee-ops-assistant:ref:refs/heads/main",
            },
          },
          Effect: "Allow",
        }),
      ],
    },
    RoleName: "employee-ops-github-ecr-publisher",
  });
  template.hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({
          Action: "ecr:GetAuthorizationToken",
          Resource: "*",
        }),
        Match.objectLike({
          Action: Match.arrayWith([
            "ecr:DescribeImages",
            "ecr:PutImage",
            "ecr:UploadLayerPart",
          ]),
          Resource: Match.arrayWith(
            Object.values(repositories).map((repository) =>
              Match.objectLike({
                "Fn::GetAtt": [
                  Match.stringLikeRegexp("Repository"),
                  "Arn",
                ],
              }),
            ),
          ),
        }),
      ]),
    },
  });
});

test("restricts Systems Manager deployment to tagged EC2 instances", () => {
  const app = new App();
  const stack = new Stack(app, "TestStack", {
    env: {
      account: "123456789012",
      region: "eu-central-1",
    },
  });
  const repositories = createApplicationRepositories(stack);
  const role = createGitHubEcrPublisherRole(stack, {
    branch: "main",
    repositories,
    repository: "Cotaie/employee-ops-assistant",
  });

  grantGitHubSsmDeploymentAccess(stack, role);

  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({
          Action: "ec2:DescribeInstances",
          Resource: "*",
        }),
        Match.objectLike({
          Action: "ssm:SendCommand",
          Resource: {
            "Fn::Join": [
              "",
              [
                "arn:",
                { Ref: "AWS::Partition" },
                ":ssm:eu-central-1::document/AWS-RunShellScript",
              ],
            ],
          },
        }),
        Match.objectLike({
          Action: "ssm:SendCommand",
          Condition: {
            StringEquals: {
              "ssm:resourceTag/EmployeeOpsDeploymentTarget": "true",
            },
          },
          Resource: {
            "Fn::Join": [
              "",
              [
                "arn:",
                { Ref: "AWS::Partition" },
                ":ec2:eu-central-1:123456789012:instance/*",
              ],
            ],
          },
        }),
        Match.objectLike({
          Action: "ssm:ListCommandInvocations",
          Resource: "*",
        }),
      ]),
    },
  });
});
