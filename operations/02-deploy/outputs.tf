output "conversational_ui_url" {
  description = "The default domain for the conversational UI app"
  value       = "https://${vercel_deployment.conversational_ui.url}"
}

output "conversational_ui_app_id" {
  description = "The ID of the App for the Conversational UI"
  value       = vercel_project.conversational_ui.id
}

output "process_queue_url" {
  value       = aws_sqs_queue.process_queue.url
  description = "URL of the SQS queue for repository processing"
}

output "api_domain_url" {
  value       = local.api_url
  description = "URL of the custom domain for the API"
}

# Information for Namecheap DNS configuration
output "api_domain_cname_target" {
  value       = aws_apigatewayv2_domain_name.api_domain.domain_name_configuration[0].target_domain_name
  description = "CNAME value to configure in Namecheap for the API domain"
}

output "api_gateway_endpoint" {
  value       = aws_apigatewayv2_stage.cudu_api.invoke_url
  description = "URL of the API Gateway endpoint"
}

output "namecheap_dns_instructions" {
  value = <<-EOT
    DNS INSTRUCTIONS FOR NAMECHEAP:
    ----------------------------------
    
    To configure the API domain, add this record in Namecheap Advanced DNS:
    
    Type: CNAME
    Host: ${replace(local.api_domain, ".umans.ai", "")}
    Value: ${aws_apigatewayv2_domain_name.api_domain.domain_name_configuration[0].target_domain_name}
    TTL: Automatic

    DNS propagation can take up to 48 hours, but usually 
    a few minutes to a few hours are sufficient.
  EOT
  description = "Instructions for DNS configuration in Namecheap"
}