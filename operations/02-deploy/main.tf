provider "aws" {
  region = "eu-west-3"
}

# Data source to access the remote state from the 01-provision layer
data "terraform_remote_state" "provision" {
  backend = "s3"
  workspace = terraform.workspace
  config = {
    bucket = "terraform-state-umans-platform"
    key    = "provision/terraform.tfstate"
    region = "eu-west-3"
  }
}

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  vercel_deployment_target       = "production"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
  conversational_ui_project_name = "conversational-ui${local.environment_name_suffix}"
  auth_url                       = "https://${local.conversational_ui_project_name}.vercel.app/api/auth/session"
}