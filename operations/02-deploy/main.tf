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
  is_production                = terraform.workspace == "production"
  pr_id                        = local.is_production ? "" : "pr-${terraform.workspace}-"
  api_domain                   = local.is_production ? "api.umans.ai" : "${local.pr_id}api.umans.ai"
  ui_domain                    = local.is_production ? "app.umans.ai" : "${local.pr_id}app.umans.ai"
  environment_name             = terraform.workspace
  deployment_target            = local.is_production ? "production" : "preview"
  vercel_deployment_target     = "production"
  environment_name_suffix      = local.is_production ? "" : "-${local.environment_name}"
  conversational_ui_project_name = "conversational-ui${local.environment_name_suffix}"
  auth_url                     = "https://${local.ui_domain}"
  api_url                      = "https://${local.api_domain}"
  certificate_arn              = data.terraform_remote_state.provision.outputs.certificate_arn
}

# Commenting out the certificate lookup as we'll use the hardcoded ARN
# data "aws_acm_certificate" "umans_ai" {
#   domain      = "umans.ai"  # Search for the exact domain
#   statuses    = ["ISSUED"]
#   types       = ["AMAZON_ISSUED"]
#   most_recent = true
# }