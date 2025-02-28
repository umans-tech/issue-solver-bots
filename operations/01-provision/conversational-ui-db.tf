terraform {
  required_providers {
    supabase = {
      source  = "supabase/supabase"
      version = "~> 1.0"
    }
  }
}

provider "supabase" {
  access_token = var.supabase_token
}

resource "random_password" "conversational_ui_db_password" {
  length  = 32
  special = false
}

resource "supabase_project" "conversational_ui" {
  organization_id   = var.supabase_organization_slug
  name              = "conversational-ui-db${local.environment_name_suffix}"
  database_password = random_password.conversational_ui_db_password.result
  region            = "eu-west-1"

  lifecycle {
    ignore_changes = [database_password]
  }
}
