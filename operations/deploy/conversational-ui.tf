terraform {
  required_providers {
    vercel = {
      source  = "vercel/vercel"
      version = "~> 2.0"
    }
  }
}

provider "vercel" {
  api_token = var.vercel_api_token
  team      = "umans"
}

resource "vercel_project" "conversational_ui" {
  name      = local.conversational_ui_project_name
  framework = "nextjs"
}

resource "vercel_project_environment_variables" "env_vars" {
  project_id = vercel_project.conversational_ui.id
  variables = [
    {
      key   = "AUTH_URL"
      value = local.auth_url
      target = [local.vercel_deployment_target]
    },
    {
      key   = "NEXT_AUTH_URL"
      value = local.auth_url
      target = [local.vercel_deployment_target]
    },
    {
      key       = "AUTH_SECRET"
      value     = var.auth_secret
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "POSTGRES_URL"
      value     = var.ui_db_url
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "BLOB_READ_WRITE_TOKEN"
      value     = var.ui_blob_read_write_token
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key   = "BLOB_ENDPOINT"
      value = var.ui_blob_endpoint
      target = [local.vercel_deployment_target]
    },
    {
      key   = "OPENAI_BASE_URL"
      value = var.openai_base_url
      target = [local.vercel_deployment_target]
    },
    {
      key       = "OPENAI_API_KEY"
      value     = var.openai_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key       = "ANTHROPIC_API_KEY"
      value     = var.anthropic_api_key
      target = [local.vercel_deployment_target]
      sensitive = true
    },
    {
      key   = "ANTHROPIC_BASE_URL"
      value = var.anthropic_base_url
      target = [local.vercel_deployment_target]
    }
  ]
}

data "vercel_project_directory" "conversational_ui" {
  path = "../../conversational-ui"
}

resource "vercel_deployment" "conversational_ui" {
  project_id  = vercel_project.conversational_ui.id
  files       = data.vercel_project_directory.conversational_ui.files
  path_prefix = data.vercel_project_directory.conversational_ui.path
  production  = local.vercel_deployment_target == "production"
}