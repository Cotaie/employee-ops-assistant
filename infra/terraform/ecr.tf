resource "aws_ecr_repository" "embeddings" {
  name                 = "embeddings"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Service   = "embeddings"
    ManagedBy = "Terraform"
  }
}

resource "aws_ecr_repository" "ingestion" {
  name                 = "ingestion"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

data "aws_ecr_image" "embeddings_latest" {
  repository_name = aws_ecr_repository.embeddings.name
  most_recent     = true
}

data "aws_ecr_image" "ingestion_latest" {
  repository_name = aws_ecr_repository.ingestion.name
  most_recent     = true
}

resource "aws_ecr_repository_policy" "embeddings_lambda_image_access" {
  repository = aws_ecr_repository.embeddings.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaToRetrieveEmbeddingsImage"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Condition = {
          ArnLike = {
            "aws:sourceArn" = "arn:aws:lambda:eu-central-1:${data.aws_caller_identity.current.account_id}:function:employee-ops-embeddings"
          }
        }
      }
    ]
  })
}

resource "aws_ecr_repository_policy" "ingestion_lambda_image_access" {
  repository = aws_ecr_repository.ingestion.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowLambdaToRetrieveIngestionImage"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Condition = {
          ArnLike = {
            "aws:sourceArn" = "arn:aws:lambda:eu-central-1:${data.aws_caller_identity.current.account_id}:function:employee-ops-ingestion"
          }
        }
      }
    ]
  })
}
