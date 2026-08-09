import { App, Stack } from "aws-cdk-lib";
import { Match, Template } from "aws-cdk-lib/assertions";
import test from "node:test";

import {
  APPLICATION_IMAGE_NAMES,
  createApplicationRepositories,
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
