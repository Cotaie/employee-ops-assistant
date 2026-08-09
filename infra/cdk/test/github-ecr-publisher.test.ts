import { App, Stack } from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import test from "node:test";

import { createApplicationRepositories } from "../lib/application-repositories";
import { createGitHubEcrPublisherRole } from "../lib/github-ecr-publisher";

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
