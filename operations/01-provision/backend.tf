terraform {
  backend "s3" {
    bucket = "terraform-state-umans-platform"
    key    = "provision/terraform.tfstate"
    region = "eu-west-3"
  }
}
