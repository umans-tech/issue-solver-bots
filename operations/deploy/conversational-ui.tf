resource "aws_amplify_app" "conversational_ui" {
  name        = "umans-conversational-ui-${local.environment_name}"
  repository  = "https://github.com/umans-tech/issue-solver-bots.git"
  oauth_token = var.github_oauth_token

  build_spec = file("${path.module}/conversational-ui-amplify-buildspec.yml")

  environment_variables = {
    AUTH_SECRET           = var.auth_secret
    POSTGRES_URL          = var.ui_db_url
    BLOB_READ_WRITE_TOKEN = var.ui_blob_read_write_token
    BLOB_ENDPOINT         = var.ui_blob_endpoint
    OPENAI_BASE_URL       = var.openai_base_url
    OPENAI_API_KEY        = var.openai_api_key
    ANTHROPIC_API_KEY     = var.anthropic_api_key
    ANTHROPIC_BASE_URL    = var.anthropic_base_url
  }
}

resource "aws_amplify_branch" "conversational_ui_branch" {
  app_id            = aws_amplify_app.conversational_ui.id
  branch_name       = var.branch_name
  enable_auto_build = true
}
