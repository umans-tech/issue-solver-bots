output "conversational_ui_url" {
  description = "The default domain for the conversational UI app"
  value       = "https://${aws_amplify_app.conversational_ui.default_domain}"
}