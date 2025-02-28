variable "branch_name" {
  type    = string
  default = "main"
}

variable "supabase_token" {
  type      = string
  sensitive = true
}

variable "supabase_organization_slug" {
  type = string
}

variable "pooler_port" {
  type        = number
  default     = 6543
  description = "Port du transaction pooler Supabase (transaction mode)"
}