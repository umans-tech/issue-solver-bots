terraform {
  backend "s3" {
    bucket = "terraform-state-umans-platform"
    key    = "foundation/apps/terraform.tfstate"
    region = "eu-west-3"
  }
}
