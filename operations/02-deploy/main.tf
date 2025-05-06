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
  domain_prefix                 = terraform.workspace == "production" ? "" : "${local.environment_name}."
  conversational_ui_project_name = "conversational-ui${local.environment_name_suffix}"
  auth_url                       = "https://app.${local.domain_prefix}umans.ai"
  
  # Verify that certificate validation has been completed
  # This will cause Terraform to fail if the certificate is not validated
  certificate_validation_check = data.terraform_remote_state.provision.outputs.certificate_validation_status == "Certificate validation completed. You can now deploy the API domain." ? true : tobool("Certificate not validated yet. Please ensure DNS records are created and wait for validation to complete.")
}

# Explicitly query the certificate to verify it's validated
data "aws_acm_certificate" "umans_ai" {
  domain      = "umans.ai"
  statuses    = ["ISSUED"]
  most_recent = true
}