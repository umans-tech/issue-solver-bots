output "conversational_ui_url" {
  description = "The default domain for the conversational UI app"
  value       = "https://${vercel_deployment.conversational_ui.url}"
}

output "conversational_ui_app_id" {
  description = "The ID of the App for the Conversational UI"
  value       = vercel_project.conversational_ui.id
}
