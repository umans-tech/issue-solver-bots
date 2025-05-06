provider "aws" {
  region = "eu-west-3"
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

data "aws_caller_identity" "current" {}

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  vercel_deployment_target       = "production"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
  conversational_ui_project_name = "conversational-ui${local.environment_name_suffix}"
  
  # Modification des domaines pour éviter les sous-domaines imbriqués
  domain_prefix                  = terraform.workspace == "production" ? "" : "${local.environment_name}-"
  ui_domain                      = "app${local.domain_prefix}umans.ai"
  api_domain                     = "api${local.domain_prefix}umans.ai"
  
  auth_url                       = "https://${local.ui_domain}"
  api_url                        = "https://${local.api_domain}"
  
  # Use certificate ARN from the provision layer
  certificate_arn = data.terraform_remote_state.provision.outputs.certificate_arn
}

# Commenting out the certificate lookup as we'll use the hardcoded ARN
# data "aws_acm_certificate" "umans_ai" {
#   domain      = "umans.ai"  # Search for the exact domain
#   statuses    = ["ISSUED"]
#   types       = ["AMAZON_ISSUED"]
#   most_recent = true
# }