import { App, Stack } from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import { Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import assert from "node:assert/strict";
import test from "node:test";

import {
  APPLICATION_IMAGE_NAMES,
  createApplicationRepositories,
  grantApplicationRepositoryPullAccess,
} from "../lib/application-repositories";

test("creates one protected ECR repository per application image", () => {
  const app = new App();
  const stack = new Stack(app, "TestStack");

  createApplicationRepositories(stack);

  const template = Template.fromStack(stack);
  template.resourceCountIs(
    "AWS::ECR::Repository",
    APPLICATION_IMAGE_NAMES.length,
  );

  for (const imageName of APPLICATION_IMAGE_NAMES) {
    template.hasResourceProperties("AWS::ECR::Repository", {
      ImageScanningConfiguration: {
        ScanOnPush: true,
      },
      ImageTagMutability: "IMMUTABLE",
      LifecyclePolicy: {
        LifecyclePolicyText: Match.serializedJson(
          Match.objectLike({
            rules: Match.arrayWith([
              Match.objectLike({
                selection: Match.objectLike({
                  countNumber: 10,
                  countType: "imageCountMoreThan",
                }),
              }),
            ]),
          }),
        ),
      },
      RepositoryName: `employee-ops-assistant/${imageName}`,
    });
  }
});

test("grants application repository pull access to a runtime role", () => {
  const app = new App();
  const stack = new Stack(app, "TestStack");
  const repositories = createApplicationRepositories(stack);
  const role = new Role(stack, "RuntimeRole", {
    assumedBy: new ServicePrincipal("ec2.amazonaws.com"),
  });

  grantApplicationRepositoryPullAccess(repositories, role);

  const template = Template.fromStack(stack);
  template.hasResourceProperties("AWS::IAM::Policy", {
    PolicyDocument: {
      Statement: Match.arrayWith([
        Match.objectLike({
          Action: "ecr:GetAuthorizationToken",
          Effect: "Allow",
          Resource: "*",
        }),
        Match.objectLike({
          Action: [
            "ecr:BatchCheckLayerAvailability",
            "ecr:GetDownloadUrlForLayer",
            "ecr:BatchGetImage",
          ],
          Effect: "Allow",
        }),
      ]),
    },
  });

  const policies = Object.values(template.findResources("AWS::IAM::Policy"));
  const statements = policies.flatMap(
    (policy) =>
      policy.Properties.PolicyDocument.Statement as Array<{
        Action: string | string[];
        Resource: unknown;
      }>,
  );
  const repositoryPullStatements = statements.filter(
    (statement) =>
      Array.isArray(statement.Action) &&
      statement.Action.includes("ecr:GetDownloadUrlForLayer"),
  );

  assert.equal(repositoryPullStatements.length, APPLICATION_IMAGE_NAMES.length);
  for (const statement of repositoryPullStatements) {
    assert.notEqual(statement.Resource, "*");
  }
  assert.equal(
    statements
      .flatMap((statement) => statement.Action)
      .some((action) =>
        [
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ].includes(action),
      ),
    false,
  );
});
