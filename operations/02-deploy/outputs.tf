# Output App Runner URL
output "conversational_ui_url" {
  description = "The URL of the App Runner service for the Conversational UI"
  value = "https://${aws_apprunner_service.conversational_ui.service_url}"
}

output "blog_url" {
  description = "The URL of the App Runner service for the Blog"
  value       = "https://${local.blog_domain}"
}

output "blog_bucket_name" {
  value       = aws_s3_bucket.blog_site.bucket
  description = "S3 bucket name for the blog static site"
}

output "blog_distribution_id" {
  value       = aws_cloudfront_distribution.blog.id
  description = "CloudFront distribution ID for cache invalidations"
}

output "process_queue_url" {
  value       = aws_sqs_queue.process_queue.url
  description = "URL of the SQS queue for repository processing"
}