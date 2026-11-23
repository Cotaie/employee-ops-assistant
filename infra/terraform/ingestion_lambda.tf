resource "aws_iam_role" "ingestion_lambda_execution" {
  name        = "employee-ops-ingestion-lambda-execution"
  description = "Execution role for the Employee Ops ingestion Lambda."

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
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

resource "aws_iam_role_policy" "ingestion_lambda_embeddings" {
  name = "invoke-embeddings-lambda"
  role = aws_iam_role.ingestion_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.embeddings.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "ingestion_lambda_sources" {
  name = "read-ingestion-sources-and-sqs-messages"
  role = aws_iam_role.ingestion_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
        ]
        Resource = "${aws_s3_bucket.ingestion_source.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = aws_sqs_queue.ingestion.arn
      },
    ]
  })
}

resource "aws_iam_role_policy" "ingestion_lambda_document_catalog" {
  name = "write-document-catalog"
  role = aws_iam_role.ingestion_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = aws_dynamodb_table.document_repository.arn
      }
    ]
  })
}

resource "aws_lambda_function" "ingestion" {
  function_name = "employee-ops-ingestion"
  description   = "Loads, chunks, and embeds documents for retrieval."
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.ingestion.repository_url}@${data.aws_ecr_image.ingestion_latest.id}"
  role          = aws_iam_role.ingestion_lambda_execution.arn

  architectures = ["x86_64"]
  memory_size   = 1024
  timeout       = 300

  environment {
    variables = {
      EMBEDDINGS_LAMBDA_FUNCTION_NAME   = aws_lambda_function.embeddings.function_name
      EMBEDDINGS_LAMBDA_REGION          = "eu-central-1"
      EMBEDDINGS_LAMBDA_TIMEOUT_SECONDS = "300"
      INGESTION_S3_REGION               = "eu-central-1"
      DOCUMENT_REPOSITORY_TABLE_NAME    = aws_dynamodb_table.document_repository.name
      DOCUMENT_REPOSITORY_REGION        = "eu-central-1"
      OPENSEARCH_COLLECTION_ENDPOINT    = aws_opensearchserverless_collection.document_repository.collection_endpoint
      OPENSEARCH_INDEX_NAME             = "document-chunks"
    }
  }

  depends_on = [
    aws_iam_role_policy.ingestion_lambda_embeddings,
    aws_iam_role_policy.ingestion_lambda_sources,
    aws_iam_role_policy.ingestion_lambda_document_catalog,
    aws_iam_role_policy.ingestion_lambda_opensearch,
    aws_opensearchserverless_access_policy.document_repository_ingestion,
    aws_ecr_repository_policy.ingestion_lambda_image_access,
  ]

  tags = {
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

output "ingestion_lambda_function_name" {
  description = "Name of the deployed ingestion Lambda function."
  value       = aws_lambda_function.ingestion.function_name
}

output "ingestion_lambda_function_arn" {
  description = "ARN of the deployed ingestion Lambda function."
  value       = aws_lambda_function.ingestion.arn
}
