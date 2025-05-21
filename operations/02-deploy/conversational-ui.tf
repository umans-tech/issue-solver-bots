terraform {
  required_providers {
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }
}

provider "vercel" {
  api_token = var.vercel_api_token
  team      = "umans"
}

resource "vercel_project" "conversational_ui" {
  name      = local.conversational_ui_project_name
  framework = "nextjs"
}

resource "vercel_project_domain" "umans_ai" {
  project_id = vercel_project.conversational_ui.id
  domain     = "${local.domain_prefix}umans.ai"
}

resource "vercel_project_domain" "app_umans_ai" {
  project_id = vercel_project.conversational_ui.id
  domain     = "app.${local.domain_prefix}umans.ai"
}

resource "vercel_project_environment_variables" "env_vars" {
  project_id = vercel_project.conversational_ui.id
  variables = [
    {
      key   = "NEXTAUTH_URL"
      value = local.auth_url
      target = [local.vercel_deployment_target]
    },
    {
      key   = "NEXTAUTH_URL_INTERNAL"
      value = "https://${local.conversational_ui_project_name}.vercel.app"
      target = [local.vercel_deployment_target]
    },
    {
      key       = "NEXTAUTH_SECRET"
      value     = var.auth_secret
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "POSTGRES_URL"
      value     = data.terraform_remote_state.provision.outputs.transaction_pooler_connection_string
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "BLOB_READ_WRITE_TOKEN"
      value     = data.terraform_remote_state.provision.outputs.blob_secret_access_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "BLOB_ACCESS_KEY_ID"
      value     = data.terraform_remote_state.provision.outputs.blob_access_key_id
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key   = "BLOB_BUCKET_NAME"
      value = data.terraform_remote_state.provision.outputs.blob_bucket_name
      target = [local.vercel_deployment_target]
    },
    {
      key   = "BLOB_REGION"
      value = data.terraform_remote_state.provision.outputs.blob_region
      target = [local.vercel_deployment_target]
    },
    {
      key   = "BLOB_ENDPOINT"
      value = "https://s3.${data.terraform_remote_state.provision.outputs.blob_region}.amazonaws.com"
      target = [local.vercel_deployment_target]
    },
    {
      key   = "OPENAI_BASE_URL"
      value = var.openai_base_url
      target = [local.vercel_deployment_target]
    },
    {
      key       = "OPENAI_API_KEY"
      value     = var.openai_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "GOOGLE_GENERATIVE_AI_API_KEY"
      value     = var.google_generative_ai_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "ANTHROPIC_API_KEY"
      value     = var.anthropic_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "EXA_API_KEY"
      value     = var.exa_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key   = "ANTHROPIC_BASE_URL"
      value = var.anthropic_base_url
      target = [local.vercel_deployment_target]
    },
    {
      key   = "CUDU_ENDPOINT"
      value = aws_apigatewayv2_api.cudu_api.api_endpoint
      target = [local.vercel_deployment_target]
    }
  ]
}

data "vercel_project_directory" "conversational_ui" {
  path = "../../conversational-ui"
}

resource "vercel_deployment" "conversational_ui" {
  project_id  = vercel_project.conversational_ui.id
  files       = data.vercel_project_directory.conversational_ui.files
  path_prefix = data.vercel_project_directory.conversational_ui.path
  production  = local.vercel_deployment_target == "production"
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

# Custom domain for App Runner (optional)
resource "aws_apprunner_custom_domain_association" "conversational_ui" {
  count = local.environment_name == "production" ? 1 : 0

  domain_name = "app-aws.umans.ai"
  service_arn = aws_apprunner_service.conversational_ui.arn

  # Note: You'll need to add the DNS verification record to your DNS provider
  # to complete the domain association
}

output "domain_validation_records" {
  value = local.environment_name == "production" ? (
    length(aws_apprunner_custom_domain_association.conversational_ui) > 0 ?
    aws_apprunner_custom_domain_association.conversational_ui[0].certificate_validation_records : null
  ) : null
  description = "DNS records for domain validation"
}
