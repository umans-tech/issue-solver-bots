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
  image_uri     = "${data.aws_caller_identity.current.account_id}.dkr.ecr.eu-west-3.amazonaws.com/umans-platform:${var.webapi_image_tag}"
  package_type  = "Image"
  role          = aws_iam_role.webapi_lambda_exec.arn
  timeout       = 60
  memory_size   = 256

  vpc_config {
    subnet_ids = data.terraform_remote_state.provision.outputs.private_subnet_ids
    security_group_ids = [data.terraform_remote_state.provision.outputs.lambda_security_group_id]
  }

  environment {
    variables = {
      DATABASE_URL                 = data.terraform_remote_state.provision.outputs.transaction_pooler_connection_string,
      OPENAI_API_KEY               = var.openai_api_key,
      ANTHROPIC_BASE_URL           = var.anthropic_base_url,
      ANTHROPIC_API_KEY            = var.anthropic_api_key,
      GOOGLE_GENERATIVE_AI_API_KEY = var.google_generative_ai_api_key,
      PROCESS_QUEUE_URL            = aws_sqs_queue.process_queue.url,
      TOKEN_ENCRYPTION_KEY         = var.token_encryption_key,
      REDIS_URL                    = data.terraform_remote_state.provision.outputs.redis_connection_string,
      NOTION_OAUTH_CLIENT_ID       = var.notion_oauth_client_id,
      NOTION_OAUTH_CLIENT_SECRET   = var.notion_oauth_client_secret,
      NOTION_OAUTH_REDIRECT_URI    = "https://${local.api_domain}/integrations/notion/oauth/callback",
      NOTION_OAUTH_RETURN_BASE_URL = "https://${local.app_domain}",
      NOTION_OAUTH_STATE_TTL_SECONDS = tostring(var.notion_oauth_state_ttl_seconds),
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

resource "aws_acm_certificate" "api_regional" {
  domain_name       = local.api_domain
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.api_regional.domain_validation_options :
    dvo.domain_name => dvo
  }

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records = [each.value.resource_record_value]
  ttl             = 60
}

resource "aws_acm_certificate_validation" "api_regional" {
  certificate_arn         = aws_acm_certificate.api_regional.arn
  validation_record_fqdns = [for rec in aws_route53_record.api_cert_validation : rec.fqdn]
}

resource "aws_apigatewayv2_domain_name" "api" {
  domain_name = local.api_domain
  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.api_regional.certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
}

resource "aws_apigatewayv2_api_mapping" "api_root" {
  api_id      = aws_apigatewayv2_api.cudu_api.id
  domain_name = aws_apigatewayv2_domain_name.api.id
  stage       = aws_apigatewayv2_stage.cudu_api.name
}

resource "aws_route53_record" "api_alias" {
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = aws_apigatewayv2_domain_name.api.domain_name
  type    = "A"
  alias {
    name                   = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api.domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = true
  }
  lifecycle {
    create_before_destroy = true
  }
}
