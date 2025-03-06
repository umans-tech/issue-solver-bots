resource "aws_s3_bucket" "conversational_ui_blob_storage" {
  bucket = "conversational-ui-blob${local.environment_name_suffix}"

  tags = {
    Name        = "Conversational UI Blob Storage"
    Environment = local.environment_name
  }
}

resource "aws_s3_bucket_ownership_controls" "conversational_ui_blob_storage" {
  bucket = aws_s3_bucket.conversational_ui_blob_storage.id
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "conversational_ui_blob_storage" {
  depends_on = [aws_s3_bucket_ownership_controls.conversational_ui_blob_storage]
  bucket     = aws_s3_bucket.conversational_ui_blob_storage.id
  acl        = "private"
}

resource "aws_iam_user" "conversational_ui_blob_user" {
  name = "conversational-ui-blob-user${local.environment_name_suffix}"
}

resource "aws_iam_access_key" "conversational_ui_blob_access_key" {
  user = aws_iam_user.conversational_ui_blob_user.name
}

resource "aws_iam_user_policy" "conversational_ui_blob_policy" {
  name = "conversational-ui-blob-policy${local.environment_name_suffix}"
  user = aws_iam_user.conversational_ui_blob_user.name

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
          aws_s3_bucket.conversational_ui_blob_storage.arn,
          "${aws_s3_bucket.conversational_ui_blob_storage.arn}/*"
        ]
      }
    ]
  })
}