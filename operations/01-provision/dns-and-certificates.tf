# ACM Certificate for *.umans.ai and umans.ai
resource "aws_acm_certificate" "umans_ai" {
  domain_name               = "umans.ai"
  subject_alternative_names = ["*.umans.ai"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Display DNS validation instructions
resource "null_resource" "dns_validation_instructions" {
  provisioner "local-exec" {
    command = <<-EOT
      echo "==================================================================="
      echo "IMPORTANT: Create the following DNS records in Namecheap:"
      %{for dvo in aws_acm_certificate.umans_ai.domain_validation_options~}
      echo "Type: ${dvo.resource_record_type}"
      echo "Host: ${replace(dvo.resource_record_name, ".umans.ai.", "")}"
      echo "Value: ${dvo.resource_record_value}"
      echo "TTL: 60"
      echo "-------------------------------------------------------------------"
      %{endfor~}
      echo "==================================================================="
    EOT
  }
}