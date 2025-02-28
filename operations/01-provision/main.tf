provider "aws" {
  region = "eu-west-3"
}

locals {
  environment_name               = terraform.workspace
  deployment_target              = terraform.workspace == "production" ? "production" : "preview"
  environment_name_suffix        = terraform.workspace == "production" ? "" : "-${local.environment_name}"
}