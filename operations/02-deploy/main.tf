terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0"
    }

    stripe = {
      source  = "lukasaron/stripe"
      version = "3.4.0"
    }
  }
}

provider "aws" {
  region = "eu-west-3"
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

provider "stripe" {
  api_key = var.stripe_secret_key
}

# Data source to access the remote state from the 01-provision layer
data "terraform_remote_state" "provision" {
  backend   = "s3"
  workspace = terraform.workspace
  config = {
    bucket = "terraform-state-umans-platform"
    key    = "provision/terraform.tfstate"
    region = "eu-west-3"
  }
}

data "terraform_remote_state" "foundation" {
  backend = "s3"
  config = {
    bucket = "terraform-state-umans-platform"
    key    = "foundation/apps/terraform.tfstate"
    region = "eu-west-3"
  }
}

data "aws_caller_identity" "current" {}

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
  domain_prefix                 = terraform.workspace == "production" ? "" : "${local.environment_name}."
  landing_domain                 = "${local.domain_prefix}umans.ai"
  app_domain                     = "app.${local.domain_prefix}umans.ai"
  api_domain                     = "api.${local.domain_prefix}umans.ai"
  blog_domain                    = "blog.${local.domain_prefix}umans.ai"
  auth_url                       = "https://${local.app_domain}"
  custom_app_runner_domains = [local.landing_domain, local.app_domain]

}