output "conversational_ui_url" {
  description = "The default domain for the conversational UI app"
  value       = "https://${aws_amplify_app.conversational_ui.default_domain}"
}

output "conversational_ui_app_id" {
  description = "The ID of the App for the Conversational UI"
  value       = aws_amplify_app.conversational_ui.id
}
