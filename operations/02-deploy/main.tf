provider "aws" {
  region = "eu-west-3"
}

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  vercel_deployment_target       = "production"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
  conversational_ui_project_name = "conversational-ui${local.environment_name_suffix}"
  auth_url                       = "https://${local.conversational_ui_project_name}.vercel.app/api/auth/session"
}