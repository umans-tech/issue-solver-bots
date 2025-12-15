terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0.0"
    }
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }
}

provider aws {
    region = "eu-west-3"
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
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
  domain_prefix                  = terraform.workspace == "production" ? "" : "${local.environment_name}."
  blog_domain                    = "blog.${local.domain_prefix}umans.ai"
}
