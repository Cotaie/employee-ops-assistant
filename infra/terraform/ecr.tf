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
