output "vercel_conversational_ui_url" {
  description = "The default domain for the conversational UI app"
  value       = "https://${vercel_deployment.conversational_ui.url}"
}

# Output App Runner URL
output "conversational_ui_url" {
  value = aws_apprunner_service.conversational_ui.service_url
}

output "conversational_ui_app_id" {
  description = "The ID of the App for the Conversational UI"
  value       = vercel_project.conversational_ui.id
}

output "process_queue_url" {
  value       = aws_sqs_queue.process_queue.url
  description = "URL of the SQS queue for repository processing"
}