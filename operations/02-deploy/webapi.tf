# IAM role for Lambda execution
resource "aws_iam_role" "webapi_lambda_exec" {
  name = "webapi${local.environment_name_suffix}-lambda-exec"

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
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.webapi_lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda function
resource "aws_lambda_function" "webapi" {
  function_name = "webapi${local.environment_name_suffix}"
  filename      = "../../issue-solver/package.zip"
  source_code_hash = filebase64sha256("../../issue-solver/package.zip")
  handler       = "issue_solver.webapi.lambda_handler.handler"
  runtime       = "python3.12"
  role          = aws_iam_role.webapi_lambda_exec.arn
  timeout       = 30
  memory_size   = 256

  environment {
    variables = {
      OPENAI_BASE_URL              = var.openai_base_url,
      OPENAI_API_KEY               = var.openai_api_key,
      ANTHROPIC_BASE_URL           = var.anthropic_base_url,
      ANTHROPIC_API_KEY            = var.anthropic_api_key,
      GOOGLE_GENERATIVE_AI_API_KEY = var.google_generative_ai_api_key,
      PROCESS_QUEUE_URL            = aws_sqs_queue.process_queue.url,
    }
  }
}

# API Gateway HTTP API
resource "aws_apigatewayv2_api" "cudu_api" {
  name          = "webapi${local.environment_name_suffix}"
  protocol_type = "HTTP"
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age = 300
  }
}

# API Gateway Lambda integration
resource "aws_apigatewayv2_integration" "cudu_api" {
  api_id           = aws_apigatewayv2_api.cudu_api.id
  integration_type = "AWS_PROXY"

  connection_type      = "INTERNET"
  description          = "Lambda integration"
  integration_method   = "POST"
  integration_uri      = aws_lambda_function.webapi.invoke_arn
  passthrough_behavior = "WHEN_NO_MATCH"
}

# API Gateway route to Lambda
resource "aws_apigatewayv2_route" "cudu_api" {
  api_id    = aws_apigatewayv2_api.cudu_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.cudu_api.id}"
}

# API Gateway stage
resource "aws_apigatewayv2_stage" "cudu_api" {
  api_id      = aws_apigatewayv2_api.cudu_api.id
  name        = "$default"
  auto_deploy = true
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webapi.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.cudu_api.execution_arn}/*/*/{proxy+}"
}