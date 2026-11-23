resource "aws_dynamodb_table" "document_repository" {
  name         = "employee-ops-document-catalog"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "source_id"

  attribute {
    name = "source_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Service   = "document-repository"
    ManagedBy = "Terraform"
  }
}

output "document_repository_table_name" {
  description = "DynamoDB table for document metadata and ingestion state."
  value       = aws_dynamodb_table.document_repository.name
}
