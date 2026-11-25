resource "aws_s3vectors_vector_bucket" "document_repository" {
  vector_bucket_name = "employee-ops-documents-vectors-${data.aws_caller_identity.current.account_id}"

  encryption_configuration {
    sse_type = "AES256"
  }

  tags = {
    Service   = "document-repository"
    ManagedBy = "Terraform"
  }
}

resource "aws_s3vectors_index" "document_chunks" {
  index_name         = "document-chunks"
  vector_bucket_name = aws_s3vectors_vector_bucket.document_repository.vector_bucket_name
  data_type          = "float32"
  dimension          = 1024
  distance_metric    = "cosine"

  metadata_configuration {
    non_filterable_metadata_keys = ["chunk_text"]
  }
}

resource "aws_iam_role_policy" "ingestion_lambda_s3_vectors" {
  name = "write-document-chunks-to-s3-vectors"
  role = aws_iam_role.ingestion_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3vectors:PutVectors"]
        Resource = aws_s3vectors_index.document_chunks.index_arn
      }
    ]
  })
}

output "document_repository_vector_bucket_name" {
  description = "S3 Vectors bucket for document chunks and embeddings."
  value       = aws_s3vectors_vector_bucket.document_repository.vector_bucket_name
}

output "document_repository_vector_index_name" {
  description = "S3 Vectors index for document chunks and embeddings."
  value       = aws_s3vectors_index.document_chunks.index_name
}
