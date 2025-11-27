resource "stripe_webhook_endpoint" "conversational_ui" {
  count       = var.stripe_webhook_enabled ? 1 : 0
  url         = "https://${local.app_domain}/api/billing/webhook"
  description = "Conversational UI billing webhook (${terraform.workspace})"

  enabled_events = [
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted"
  ]
}

resource "aws_secretsmanager_secret" "stripe_webhook_secret" {
  count       = var.stripe_webhook_enabled ? 1 : 0
  name        = "conversational-ui-stripe-webhook${local.environment_name_suffix}"
  description = "Stripe webhook signing secret for conversational UI"
}

resource "aws_secretsmanager_secret_version" "stripe_webhook_secret_current" {
  count         = var.stripe_webhook_enabled ? 1 : 0
  secret_id     = aws_secretsmanager_secret.stripe_webhook_secret[0].id
  secret_string = stripe_webhook_endpoint.conversational_ui[0].secret
}


