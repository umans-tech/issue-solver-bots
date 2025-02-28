terraform {
  backend "s3" {
    bucket = "terraform-state-umans-platform"
    key    = "deploy/apps/terraform.tfstate"
    region = "eu-west-3"
  }
}
