resource "aws_opensearchserverless_security_policy" "document_repository_encryption" {
  name        = "employee-ops-os-encryption"
  type        = "encryption"
  description = "Encryption policy for the document repository vector collection."

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/employee-ops-documents"]
      }
    ]
    AWSOwnedKey = true
  })
}

resource "aws_opensearchserverless_security_policy" "document_repository_network" {
  name        = "employee-ops-os-network"
  type        = "network"
  description = "Network policy for the document repository collection API."

  policy = jsonencode([
    {
      Description = "Public network path for the IAM-authorized collection API."
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/employee-ops-documents"]
        }
      ]
      AllowFromPublic = true
    }
  ])
}

resource "aws_opensearchserverless_collection" "document_repository" {
  name        = "employee-ops-documents"
  description = "Vector index for document repository chunks and embeddings."
  type        = "VECTORSEARCH"
  # Keep standby replicas off for the initial low-volume environment; enable for HA.
  standby_replicas = "DISABLED"

  tags = {
    Service   = "document-repository"
    ManagedBy = "Terraform"
  }

  depends_on = [
    aws_opensearchserverless_security_policy.document_repository_encryption,
    aws_opensearchserverless_security_policy.document_repository_network,
  ]
}

resource "aws_opensearchserverless_access_policy" "document_repository_ingestion" {
  name        = "employee-ops-os-ingestion"
  type        = "data"
  description = "Allow ingestion Lambda to create and write the document chunks index."

  policy = jsonencode([
    {
      Description = "Ingestion Lambda can create and write document chunks."
      Principal   = [aws_iam_role.ingestion_lambda_execution.arn]
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${aws_opensearchserverless_collection.document_repository.name}"]
          Permission   = ["aoss:DescribeCollectionItems"]
        },
        {
          ResourceType = "index"
          Resource     = ["index/${aws_opensearchserverless_collection.document_repository.name}/document-chunks"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DescribeIndex",
            "aoss:UpdateIndex",
            "aoss:WriteDocument",
          ]
        }
      ]
    }
  ])

  depends_on = [aws_opensearchserverless_collection.document_repository]
}

resource "aws_iam_role_policy" "ingestion_lambda_opensearch" {
  name = "write-document-chunks-to-opensearch"
  role = aws_iam_role.ingestion_lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["aoss:APIAccessAll"]
        Resource = aws_opensearchserverless_collection.document_repository.arn
      }
    ]
  })
}

output "document_repository_opensearch_collection_name" {
  description = "OpenSearch Serverless collection for document chunks and embeddings."
  value       = aws_opensearchserverless_collection.document_repository.name
}

output "document_repository_opensearch_collection_endpoint" {
  description = "OpenSearch Serverless API endpoint for document repository indexing and search."
  value       = aws_opensearchserverless_collection.document_repository.collection_endpoint
}
