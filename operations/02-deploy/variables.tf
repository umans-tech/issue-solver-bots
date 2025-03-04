variable "auth_secret" {
  type      = string
  sensitive = true
}

variable "aws_access_key_id" {
  type      = string
  sensitive = true
  default   = ""
}

variable "aws_secret_access_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "s3_bucket_name" {
  type      = string
  sensitive = true
  default   = ""
}

variable "s3_aws_region" {
  type      = string
  sensitive = true
  default   = ""
}

variable "aws_endpoint" {
  type      = string
  sensitive = true
  default   = ""
}

variable "ui_blob_read_write_token" {
  type      = string
  sensitive = true
}

variable "ui_blob_endpoint" {
  type = string
}

variable "branch_name" {
  type    = string
  default = "main"
}

variable "openai_base_url" {
  type    = string
  default = ""
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "google_generative_ai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "anthropic_base_url" {
  type    = string
  default = ""
}

variable "anthropic_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "vercel_api_token" {
  description = "Vercel API Token"
  type        = string
  sensitive = true
}