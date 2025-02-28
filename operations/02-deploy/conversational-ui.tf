resource "aws_iam_role" "conversational_ui_amplify_role" {
  name = "umans-conversational-ui-amplify-role-${local.environment_name}"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "amplify.eu-west-3.amazonaws.com",
            "amplify.amazonaws.com",
            "codebuild.eu-west-3.amazonaws.com",
            "codebuild.amazonaws.com"
          ]
        }
        Action = [
          "sts:AssumeRole",
          "sts:TagSession"
        ]
      }
    ]
  })
}

data "aws_iam_policy" "administrator_access_amplify" {
  name = "AdministratorAccess-Amplify"
}

resource "aws_iam_role_policy_attachment" "conversational_ui_amplify_attach" {
  role       = aws_iam_role.conversational_ui_amplify_role.name
  policy_arn = data.aws_iam_policy.administrator_access_amplify.arn
}

resource "aws_amplify_app" "conversational_ui" {
  name                 = "umans-conversational-ui${local.environment_name_suffix}"
  platform             = "WEB_COMPUTE"
  repository           = "https://github.com/umans-tech/issue-solver-bots.git"
  oauth_token          = var.github_oauth_token
  iam_service_role_arn = aws_iam_role.conversational_ui_amplify_role.arn

  build_spec = file("${path.module}/conversational-ui-amplify-buildspec.yml")
  environment_variables = {
    AMPLIFY_MONOREPO_APP_ROOT = "conversational-ui"
  }
}

resource "aws_amplify_branch" "conversational_ui_branch" {
  app_id            = aws_amplify_app.conversational_ui.id
  framework         = "Next.js - SSR"
  branch_name       = var.branch_name
  enable_auto_build = true
  environment_variables = {
    AMPLIFY_MONOREPO_APP_ROOT = "conversational-ui"
    AUTH_URL                  = "https://${replace(var.branch_name, "/", "-")}.${aws_amplify_app.conversational_ui.default_domain}/api/auth/session"
    NEXT_AUTH_URL             = "https://${replace(var.branch_name, "/", "-")}.${aws_amplify_app.conversational_ui.default_domain}/api/auth/session"
    AUTH_SECRET               = var.auth_secret
    POSTGRES_URL              = var.ui_db_url
    BLOB_READ_WRITE_TOKEN     = var.ui_blob_read_write_token
    BLOB_ENDPOINT             = var.ui_blob_endpoint
    OPENAI_BASE_URL           = var.openai_base_url
    OPENAI_API_KEY            = var.openai_api_key
    ANTHROPIC_API_KEY         = var.anthropic_api_key
    ANTHROPIC_BASE_URL        = var.anthropic_base_url
  }
}