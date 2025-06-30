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

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
}