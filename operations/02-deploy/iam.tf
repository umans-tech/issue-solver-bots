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