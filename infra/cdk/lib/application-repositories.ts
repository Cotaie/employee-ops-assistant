import { RemovalPolicy } from "aws-cdk-lib";
import {
  Repository,
  TagMutability,
  type IRepository,
} from "aws-cdk-lib/aws-ecr";
import type { IGrantable } from "aws-cdk-lib/aws-iam";
import type { Construct } from "constructs";

export const APPLICATION_IMAGE_NAMES = [
  "agent-api",
  "embeddings-api",
  "gradio-ui",
  "ingestion-api",
  "retrieve-api",
] as const;

export type ApplicationImageName = (typeof APPLICATION_IMAGE_NAMES)[number];
export type ApplicationRepositories = Readonly<
  Record<ApplicationImageName, IRepository>
>;

function createRepository(
  scope: Construct,
  id: string,
  imageName: ApplicationImageName,
): IRepository {
  return new Repository(scope, id, {
    imageScanOnPush: true,
    imageTagMutability: TagMutability.IMMUTABLE,
    lifecycleRules: [
      {
        description: "Keep the ten most recent application images",
        maxImageCount: 10,
      },
    ],
    removalPolicy: RemovalPolicy.RETAIN,
    repositoryName: `employee-ops-assistant/${imageName}`,
  });
}

export function createApplicationRepositories(
  scope: Construct,
): ApplicationRepositories {
  return {
    "agent-api": createRepository(scope, "AgentApiRepository", "agent-api"),
    "embeddings-api": createRepository(
      scope,
      "EmbeddingsApiRepository",
      "embeddings-api",
    ),
    "gradio-ui": createRepository(scope, "GradioUiRepository", "gradio-ui"),
    "ingestion-api": createRepository(
      scope,
      "IngestionApiRepository",
      "ingestion-api",
    ),
    "retrieve-api": createRepository(
      scope,
      "RetrieveApiRepository",
      "retrieve-api",
    ),
  };
}

export function grantApplicationRepositoryPullAccess(
  repositories: ApplicationRepositories,
  grantee: IGrantable,
): void {
  for (const repository of Object.values(repositories)) {
    repository.grantPull(grantee);
  }
}
