# Local variables
locals {
  # AWS typically creates 3 certificate validation records per domain
  # If you encounter errors about index out of bounds, you may need to adjust this number
  # This is a workaround for Terraform's limitation with for_each and unknown values
  # See: https://github.com/hashicorp/terraform-provider-aws/issues/23460
  cert_validation_records_count = 3
}

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

# Allow App Runner to retrieve secrets from Secrets Manager when the Stripe webhook is managed
resource "aws_iam_role_policy" "conversational_ui_stripe_secret_access" {
  count = var.stripe_webhook_enabled ? 1 : 0

  name = "conversational-ui${local.environment_name_suffix}-stripe-webhook-secret-access"
  role = aws_iam_role.conversational_ui_app_runner_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = aws_secretsmanager_secret.stripe_webhook_secret[0].arn
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
  security_groups    = [data.terraform_remote_state.provision.outputs.lambda_security_group_id]
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
          AUTH_GOOGLE_ID               = var.auth_google_id
          AUTH_GOOGLE_SECRET           = var.auth_google_secret
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
          EMAIL_API_KEY                = var.email_api_key
          EMAIL_FROM                   = var.email_from
          POSTHOG_KEY                  = var.posthog_key
          POSTHOG_HOST                 = var.posthog_host
          STRIPE_SECRET_KEY            = var.stripe_secret_key
          STRIPE_BILLING_PORTAL_URL    = var.stripe_billing_portal_url
        }

        runtime_environment_secrets = var.stripe_webhook_enabled ? {
          STRIPE_WEBHOOK_SECRET = aws_secretsmanager_secret.stripe_webhook_secret[0].arn
        } : {}
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

# Create validation records for the landing domain (typically 3 records)
# WORKAROUND: We use count with tolist() instead of for_each to avoid the Terraform error:
# "Invalid for_each argument: certificate_validation_records will be known only after apply"
# This is a known limitation when using for_each with unknown values from resource attributes
resource "aws_route53_record" "apprunner_cert_validation_landing" {
  count = local.cert_validation_records_count

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = tolist(aws_apprunner_custom_domain_association.conversational_ui[local.landing_domain].certificate_validation_records)[count.index].name
  type            = tolist(aws_apprunner_custom_domain_association.conversational_ui[local.landing_domain].certificate_validation_records)[count.index].type
  records = [
    tolist(aws_apprunner_custom_domain_association.conversational_ui[local.landing_domain].certificate_validation_records)[count.index].value
  ]
  ttl = 60
}

# Create validation records for the app domain (typically 3 records)
# WORKAROUND: Same as above - using count with tolist() instead of for_each
resource "aws_route53_record" "apprunner_cert_validation_app" {
  count = local.cert_validation_records_count

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = tolist(aws_apprunner_custom_domain_association.conversational_ui[local.app_domain].certificate_validation_records)[count.index].name
  type            = tolist(aws_apprunner_custom_domain_association.conversational_ui[local.app_domain].certificate_validation_records)[count.index].type
  records = [
    tolist(aws_apprunner_custom_domain_association.conversational_ui[local.app_domain].certificate_validation_records)[count.index].value
  ]
  ttl = 60
}

# Create CNAME records for subdomains and alias record for apex domain
resource "aws_route53_record" "landing_alias" {
  # Skip landing domain when CloudFront handles it (all environments)
  for_each = {
    for domain, assoc in aws_apprunner_custom_domain_association.conversational_ui : domain => assoc
    if domain != local.landing_domain
  }

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.value.domain_name

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
