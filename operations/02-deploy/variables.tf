variable "auth_secret" {
  type      = string
  sensitive = true
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

variable "exa_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "vercel_api_token" {
  description = "Vercel API Token"
  type        = string
  sensitive   = true
}

variable "webapi_image_tag" {
  type        = string
  description = "The tag of the Docker image to be deployed in the webapi lambda function"
}

variable "worker_image_tag" {
  type        = string
  description = "The tag of the Docker image to be deployed in the worker lambda function"
}