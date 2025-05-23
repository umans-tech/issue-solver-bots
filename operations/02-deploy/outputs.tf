# Output App Runner URL
output "conversational_ui_url" {
  description = "The URL of the App Runner service for the Conversational UI"
  value = "https://${aws_apprunner_service.conversational_ui.service_url}"
}

output "process_queue_url" {
  value       = aws_sqs_queue.process_queue.url
  description = "URL of the SQS queue for repository processing"
}