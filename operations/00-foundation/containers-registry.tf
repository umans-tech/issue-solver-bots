# Create an Elastic Container Registry repository
resource "aws_ecr_repository" "app_repository" {
  name                 = "umans-platform"
  image_tag_mutability = "MUTABLE"

  encryption_configuration {
    encryption_type = "KMS"
  }

  tags = {
    Name        = "umans-platform"
    Environment = "foundation"
    Terraform   = "true"
  }
}

# Lifecycle policy to manage image retention
resource "aws_ecr_lifecycle_policy" "app_lifecycle_policy" {
  repository = aws_ecr_repository.app_repository.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Retain production tagged images"
        selection = {
          tagStatus = "tagged"
          tagPrefixList = [
            "umans-platform-webapi-production",
            "umans-platform-worker-production"
          ]
          countType   = "imageCountMoreThan"
          countNumber = 12
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Keep last 10 images for non-production tagged images"
        selection = {
          tagStatus = "tagged"
          tagPrefixList = [
            "umans-platform-webapi-pr-",
            "umans-platform-worker-pr-"
          ]
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Expire untagged images older than 7 days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countNumber = 7
          countUnit   = "days"
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}