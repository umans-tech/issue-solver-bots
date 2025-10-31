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

variable "morph_api_key" {
  type        = string
  sensitive   = true
  description = "API key for Morph Cloud Micro VMs service"
}

variable "dev_environment_service_enabled" {
  type        = bool
  default     = true
  description = "Flag to enable or disable the Dev Environment Service"
}

variable "posthog_key" {
  description = "PostHog project API key"
  type        = string
  sensitive   = true
}

variable "posthog_host" {
  description = "PostHog instance host URL"
  type        = string
  default     = "https://eu.i.posthog.com"
}

variable "notion_mcp_client_id" {
  description = "Client ID for the Notion MCP integration"
  type        = string
  sensitive   = true
}

variable "notion_mcp_client_secret" {
  description = "Client secret for the Notion MCP integration"
  type        = string
  sensitive   = true
}

variable "notion_mcp_state_ttl_seconds" {
  description = "TTL (in seconds) for MCP OAuth state stored in Redis"
  type        = number
  default     = 600
}

variable "stripe_secret_key" {
  description = "Stripe secret key for payment processing"
  type        = string
  sensitive   = true
  default     = ""
}

variable "stripe_webhook_enabled" {
  description = "Whether to manage the Stripe webhook endpoint via Terraform"
  type        = bool
  default     = true
}

variable "stripe_billing_portal_url" {
  description = "URL for the Stripe billing portal"
  type        = string
  default     = ""
}
