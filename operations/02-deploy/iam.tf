# IAM policy to allow Lambda to create network interfaces in the VPC
resource "aws_iam_policy" "lambda_vpc_access" {
  name        = "lambda-vpc-access${local.environment_name_suffix}"
  description = "IAM policy for Lambda VPC access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# IAM policy to allow worker Lambda to access the knowledge blob S3 bucket
resource "aws_iam_policy" "worker_blob_s3_access" {
  name        = "worker-blob-s3-access${local.environment_name_suffix}"
  description = "Allow worker Lambda to read/write in knowledge blob S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${data.terraform_remote_state.provision.outputs.blob_bucket_name}"
      },
      {
        Sid    = "ObjectRW"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "arn:aws:s3:::${data.terraform_remote_state.provision.outputs.blob_bucket_name}/*"
      }
    ]
  })
}

# Attach S3 access policy to worker execution role
resource "aws_iam_role_policy_attachment" "worker_blob_s3_access" {
  role       = aws_iam_role.worker_lambda_exec.name
  policy_arn = aws_iam_policy.worker_blob_s3_access.arn
}

# Attach policy to webapi execution role
resource "aws_iam_role_policy_attachment" "webapi_vpc_access" {
  role       = aws_iam_role.webapi_lambda_exec.name
  policy_arn = aws_iam_policy.lambda_vpc_access.arn
}

# Attach policy to worker execution role
resource "aws_iam_role_policy_attachment" "worker_vpc_access" {
  role       = aws_iam_role.worker_lambda_exec.name
  policy_arn = aws_iam_policy.lambda_vpc_access.arn
}
