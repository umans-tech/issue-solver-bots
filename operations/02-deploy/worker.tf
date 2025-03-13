resource "aws_lambda_function" "worker" {
  function_name = "worker${local.environment_name_suffix}"
  image_uri     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.eu-west-3.amazonaws.com/umans-platform:${var.worker_image_tag}"
  package_type  = "Image"
  role          = aws_iam_role.worker_lambda_exec.arn
  timeout = 300  # 5 minutes
  memory_size   = 512

  environment {
    variables = {
      OPENAI_BASE_URL              = var.openai_base_url,
      OPENAI_API_KEY               = var.openai_api_key,
      ANTHROPIC_BASE_URL           = var.anthropic_base_url,
      ANTHROPIC_API_KEY            = var.anthropic_api_key,
      GOOGLE_GENERATIVE_AI_API_KEY = var.google_generative_ai_api_key,
    }
  }
}

resource "aws_iam_role" "worker_lambda_exec" {
  name = "worker${local.environment_name_suffix}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "process_lambda_basic" {
  role       = aws_iam_role.worker_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach SQS policy to process Lambda execution role
resource "aws_iam_role_policy_attachment" "process_lambda_sqs" {
  role       = aws_iam_role.worker_lambda_exec.name
  policy_arn = aws_iam_policy.lambda_sqs_policy.arn
}

# Event source mapping to trigger Lambda from SQS
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.process_queue.arn
  function_name    = aws_lambda_function.worker.function_name
  batch_size       = 1
  enabled          = true
} 