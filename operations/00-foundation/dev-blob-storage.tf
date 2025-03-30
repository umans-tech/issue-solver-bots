resource "aws_s3_bucket" "development_blob_storage" {
  bucket = "umans-dev"

  tags = {
    Name        = "Multi purpose blob storage for development"
    Environment = "development"
  }
}

resource "aws_s3_bucket_ownership_controls" "development_blob_storage" {
  bucket = aws_s3_bucket.development_blob_storage.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "development_blob_storage" {
  depends_on = [aws_s3_bucket_ownership_controls.development_blob_storage]
  bucket     = aws_s3_bucket.development_blob_storage.id
  acl        = "private"
}
resource "aws_iam_user" "dev_blob_user" {
  name = "dev-blob-user"
}

resource "aws_iam_access_key" "dev_blob_access_key" {
  user = aws_iam_user.dev_blob_user.name
}

resource "aws_iam_user_policy" "dev_blob_policy" {
  name = "dev-blob-policy"
  user = aws_iam_user.dev_blob_user.name

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
          aws_s3_bucket.development_blob_storage.arn,
          "${aws_s3_bucket.development_blob_storage.arn}/*"
        ]
      }
    ]
  })
}

output "blob_bucket_name" {
  value = aws_s3_bucket.development_blob_storage.bucket
}

output "blob_region" {
  value = "eu-west-3"
}

output "blob_access_key_id" {
  value = aws_iam_access_key.dev_blob_access_key.id
  sensitive = true
}

output "blob_secret_access_key" {
  value = aws_iam_access_key.dev_blob_access_key.secret
  sensitive = true
}