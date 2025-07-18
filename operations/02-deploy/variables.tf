variable "auth_secret" {
  type      = string
  sensitive = true
}
variable "auth_google_id" {
  type      = string
  sensitive = true
}

variable "auth_google_secret" {
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

variable "webapi_image_tag" {
  type        = string
  description = "The tag of the Docker image to be deployed in the webapi lambda function"
}

variable "worker_image_tag" {
  type        = string
  description = "The tag of the Docker image to be deployed in the worker lambda function"
}

variable "conversational_ui_image_tag" {
  type        = string
  description = "The tag of the Docker image to be deployed in the conversational-ui App Runner service"
}

variable "email_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "email_from" {
  type    = string
  default = "noreply@umans.ai"
}

variable "token_encryption_key" {
  type        = string
  sensitive   = true
  description = "Encryption key for securing access tokens in the database"
}