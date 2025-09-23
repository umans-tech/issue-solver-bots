resource "aws_s3_bucket" "knowledge_blob_storage" {
  bucket = "knowledge-blob${local.environment_name_suffix}"

  tags = {
    Name        = "Knowledge Blob Storage"
    Environment = local.environment_name
  }
}

resource "aws_s3_bucket_ownership_controls" "knowledge_blob_storage" {
  bucket = aws_s3_bucket.knowledge_blob_storage.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "knowledge_blob_storage" {
  depends_on = [aws_s3_bucket_ownership_controls.knowledge_blob_storage]
  bucket     = aws_s3_bucket.knowledge_blob_storage.id
  acl        = "private"
}

resource "aws_iam_user" "knowledge_blob_user" {
  name = "knowledge-blob-user${local.environment_name_suffix}"
}

resource "aws_iam_access_key" "knowledge_blob_access_key" {
  user = aws_iam_user.knowledge_blob_user.name
}

resource "aws_iam_user_policy" "knowledge_blob_policy" {
  name = "knowledge-blob-policy${local.environment_name_suffix}"
  user = aws_iam_user.knowledge_blob_user.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:DeleteObject"
        ]
        Effect   = "Allow"
        Resource = [
          aws_s3_bucket.knowledge_blob_storage.arn,
          "${aws_s3_bucket.knowledge_blob_storage.arn}/*"
        ]
      }
    ]
  })
}