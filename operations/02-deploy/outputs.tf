# Output App Runner URL
output "conversational_ui_url" {
  description = "The URL of the App Runner service for the Conversational UI"
  value       = "https://${aws_apprunner_service.conversational_ui.service_url}"
}

output "blog_url" {
  description = "The URL of the Blog (managed in provision layer)"
  value       = data.terraform_remote_state.provision.outputs.blog_url
}

output "blog_bucket_name" {
  value       = data.terraform_remote_state.provision.outputs.blog_bucket_name
  description = "S3 bucket name for the blog static site"
}

output "blog_distribution_id" {
  value       = data.terraform_remote_state.provision.outputs.blog_distribution_id
  description = "CloudFront distribution ID for cache invalidations"
}

output "process_queue_url" {
  value       = aws_sqs_queue.process_queue.url
  description = "URL of the SQS queue for repository processing"
}
