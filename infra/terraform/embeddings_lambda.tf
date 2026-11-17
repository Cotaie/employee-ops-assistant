resource "aws_iam_role" "embeddings_lambda_execution" {
  name        = "employee-ops-embeddings-lambda-execution"
  description = "Execution role for the Employee Ops embeddings Lambda."

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Service   = "embeddings"
    ManagedBy = "Terraform"
  }
}

resource "aws_iam_role_policy" "embeddings_lambda_bedrock" {
  name = "invoke-titan-embeddings-model"
  role = aws_iam_role.embeddings_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = "arn:aws:bedrock:eu-central-1::foundation-model/amazon.titan-embed-text-v2:0"
      }
    ]
  })
}

resource "aws_lambda_function" "embeddings" {
  function_name = "employee-ops-embeddings"
  description   = "Generates Titan Text Embeddings V2 vectors for application services."
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.embeddings.repository_url}@${data.aws_ecr_image.embeddings_latest.id}"
  role          = aws_iam_role.embeddings_lambda_execution.arn

  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = 300

  environment {
    variables = {
      MODEL_NAME              = "amazon.titan-embed-text-v2:0"
      BEDROCK_REGION          = "eu-central-1"
      BEDROCK_DIMENSIONS      = "1024"
      BEDROCK_MAX_CONCURRENCY = "4"
    }
  }

  depends_on = [
    aws_iam_role_policy.embeddings_lambda_bedrock,
    aws_ecr_repository_policy.embeddings_lambda_image_access,
  ]

  tags = {
    Service   = "embeddings"
    ManagedBy = "Terraform"
  }
}

output "embeddings_lambda_function_name" {
  description = "Name of the deployed embeddings Lambda function."
  value       = aws_lambda_function.embeddings.function_name
}

output "embeddings_lambda_function_arn" {
  description = "ARN of the deployed embeddings Lambda function."
  value       = aws_lambda_function.embeddings.arn
}
