resource "aws_s3_bucket" "ingestion_source" {
  bucket = "employee-ops-ingestion-source-${data.aws_caller_identity.current.account_id}"

  tags = {
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

resource "aws_s3_bucket_public_access_block" "ingestion_source" {
  bucket                  = aws_s3_bucket.ingestion_source.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ingestion_source" {
  bucket = aws_s3_bucket.ingestion_source.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_sqs_queue" "ingestion_dlq" {
  name                      = "employee-ops-ingestion-dlq"
  message_retention_seconds = 1209600

  tags = {
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

resource "aws_sqs_queue" "ingestion" {
  name                       = "employee-ops-ingestion"
  visibility_timeout_seconds = 1800
  message_retention_seconds  = 345600
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.ingestion_dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Service   = "ingestion"
    ManagedBy = "Terraform"
  }
}

resource "aws_sqs_queue_policy" "ingestion_s3_send" {
  queue_url = aws_sqs_queue.ingestion.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowIngestionSourceBucketToPublish"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.ingestion.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_s3_bucket.ingestion_source.arn
          }
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_notification" "ingestion_source" {
  bucket = aws_s3_bucket.ingestion_source.id

  queue {
    queue_arn = aws_sqs_queue.ingestion.arn
    events    = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_sqs_queue_policy.ingestion_s3_send]
}

resource "aws_lambda_event_source_mapping" "ingestion_sqs" {
  event_source_arn = aws_sqs_queue.ingestion.arn
  function_name    = aws_lambda_function.ingestion.arn
  batch_size       = 1
  enabled          = true

  function_response_types = ["ReportBatchItemFailures"]

  depends_on = [aws_iam_role_policy.ingestion_lambda_sources]
}

output "ingestion_source_bucket_name" {
  description = "S3 bucket that accepts source documents for ingestion."
  value       = aws_s3_bucket.ingestion_source.id
}

output "ingestion_queue_url" {
  description = "SQS queue URL that triggers the ingestion Lambda."
  value       = aws_sqs_queue.ingestion.id
}

output "ingestion_dlq_url" {
  description = "SQS dead-letter queue URL for failed ingestion messages."
  value       = aws_sqs_queue.ingestion_dlq.id
}
