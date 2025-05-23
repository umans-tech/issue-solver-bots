# IAM role for App Runner
resource "aws_iam_role" "conversational_ui_app_runner_role" {
  name = "conversational-ui${local.environment_name_suffix}-app-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "build.apprunner.amazonaws.com",
            "tasks.apprunner.amazonaws.com",
            "apprunner.amazonaws.com"
          ]
        }
      }
    ]
  })
}

# Policy for ECR access
resource "aws_iam_role_policy_attachment" "app_runner_ecr_policy" {
  role       = aws_iam_role.conversational_ui_app_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# App Runner VPC connector to access private resources
resource "aws_apprunner_vpc_connector" "conversational_ui_vpc_connector" {
  vpc_connector_name = "conversational-ui${local.environment_name_suffix}-vpc-connector"
  subnets            = data.terraform_remote_state.provision.outputs.private_subnet_ids
  security_groups = [data.terraform_remote_state.provision.outputs.lambda_security_group_id]
}

# App Runner service
resource "aws_apprunner_service" "conversational_ui" {
  service_name = "conversational-ui${local.environment_name_suffix}"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.conversational_ui_app_runner_role.arn
    }

    image_repository {
      image_configuration {
        port = 3000
        runtime_environment_variables = {
          NODE_ENV                     = "production"
          HOSTNAME                     = "0.0.0.0"
          POSTGRES_URL                 = data.terraform_remote_state.provision.outputs.transaction_pooler_connection_string
          NEXTAUTH_URL                 = local.auth_url
          NEXTAUTH_SECRET              = var.auth_secret
          REDIS_URL                    = data.terraform_remote_state.provision.outputs.redis_connection_string
          BLOB_READ_WRITE_TOKEN        = data.terraform_remote_state.provision.outputs.blob_secret_access_key
          BLOB_ACCESS_KEY_ID           = data.terraform_remote_state.provision.outputs.blob_access_key_id
          BLOB_BUCKET_NAME             = data.terraform_remote_state.provision.outputs.blob_bucket_name
          BLOB_REGION                  = data.terraform_remote_state.provision.outputs.blob_region
          BLOB_ENDPOINT                = "https://s3.${data.terraform_remote_state.provision.outputs.blob_region}.amazonaws.com"
          OPENAI_BASE_URL              = var.openai_base_url
          OPENAI_API_KEY               = var.openai_api_key
          GOOGLE_GENERATIVE_AI_API_KEY = var.google_generative_ai_api_key
          ANTHROPIC_API_KEY            = var.anthropic_api_key
          ANTHROPIC_BASE_URL           = var.anthropic_base_url
          EXA_API_KEY                  = var.exa_api_key
          CUDU_ENDPOINT                = aws_apigatewayv2_api.cudu_api.api_endpoint
        }
      }
      image_identifier      = "${data.aws_caller_identity.current.account_id}.dkr.ecr.eu-west-3.amazonaws.com/umans-platform:${var.conversational_ui_image_tag}"
      image_repository_type = "ECR"
    }
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/api/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }


  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.conversational_ui_vpc_connector.arn
    }
  }

  instance_configuration {
    cpu               = "1 vCPU"
    memory            = "2 GB"
    instance_role_arn = aws_iam_role.conversational_ui_app_runner_role.arn
  }

  tags = {
    Name        = "conversational-ui${local.environment_name_suffix}"
    Environment = local.deployment_target
  }
}

resource "aws_apprunner_custom_domain_association" "conversational_ui" {
  for_each    = toset(local.custom_app_runner_domains)
  service_arn = aws_apprunner_service.conversational_ui.arn
  domain_name = each.value
}

locals {
  apprunner_cert_validations = flatten([
    for domain_key, domain_assoc in aws_apprunner_custom_domain_association.conversational_ui : [
      for cert_record in domain_assoc.certificate_validation_records : {
        key    = "${domain_key}-${cert_record.name}"
        name   = cert_record.name
        type   = cert_record.type
        value  = cert_record.value
      }
    ]
  ])
}

resource "aws_route53_record" "apprunner_cert_validation" {
  for_each = {
    for validation in local.apprunner_cert_validations :
    validation.key => validation
  }

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.value]
  ttl             = 60
}

# Create CNAME records for subdomains and alias record for apex domain
resource "aws_route53_record" "landing_alias" {
  for_each = aws_apprunner_custom_domain_association.conversational_ui

  allow_overwrite = true
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = each.value.domain_name
  
  # Use alias record for apex domain, CNAME for subdomains
  type = each.value.domain_name == "umans.ai" ? "A" : "CNAME"
  
  # For apex domain (umans.ai), use alias record
  dynamic "alias" {
    for_each = each.value.domain_name == "umans.ai" ? [1] : []
    content {
      name                   = each.value.dns_target
      zone_id                = "Z087117439MBKHYM69QS6" # App Runner hosted zone ID for eu-west-3
      evaluate_target_health = false
    }
  }
  
  # For subdomains, use CNAME records
  ttl     = each.value.domain_name == "umans.ai" ? null : 300
  records = each.value.domain_name == "umans.ai" ? null : [each.value.dns_target]
  
  lifecycle {
    create_before_destroy = true
  }
}

