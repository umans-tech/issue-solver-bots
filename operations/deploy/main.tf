provider "aws" {
  region = "eu-west-3"
}

locals {
  environment_name = terraform.workspace
}