# SQS Queue for repository processing
resource "aws_sqs_queue" "process_queue" {
  name                       = "process-queue${local.environment_name_suffix}"
  visibility_timeout_seconds = 300
}

# IAM policy for Lambda to access SQS
resource "aws_iam_policy" "lambda_sqs_policy" {
  name        = "process-queue${local.environment_name_suffix}-lambda-sqs-policy"
  description = "IAM policy for Lambda to access SQS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Effect   = "Allow"
        Resource = aws_sqs_queue.process_queue.arn
      }
    ]
  })
}

# Attach SQS policy to Lambda execution role
resource "aws_iam_role_policy_attachment" "webapi_sqs" {
  role       = aws_iam_role.webapi_lambda_exec.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}
