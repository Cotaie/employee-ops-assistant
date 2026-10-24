resource "aws_iam_role" "github_embeddings_ecr_publisher" {
  name        = "employee-ops-embeddings-ecr-publisher"
  description = "Allows the embeddings image workflow on main to push to ECR"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github_actions.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:Cotaie/employee-ops-assistant:ref:refs/heads/main"
          }
        }
      }
    ]
  })

  tags = {
    Service   = "embeddings"
    ManagedBy = "Terraform"
  }
}

resource "aws_iam_role_policy" "github_embeddings_ecr_push" {
  name = "push-embeddings-image"
  role = aws_iam_role.github_embeddings_ecr_publisher.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Resource = aws_ecr_repository.embeddings.arn
      },
    ]
  })
}

output "github_embeddings_ecr_publisher_role_arn" {
  description = "IAM role assumed by GitHub Actions to push the embeddings image"
  value       = aws_iam_role.github_embeddings_ecr_publisher.arn
}
