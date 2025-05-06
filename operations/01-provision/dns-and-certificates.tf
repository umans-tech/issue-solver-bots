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

# Wait for certificate validation
# Note: This makes Terraform wait for the certificate to be validated
# You'll need to manually create the DNS records in Namecheap
resource "aws_acm_certificate_validation" "umans_ai" {
  certificate_arn = aws_acm_certificate.umans_ai.arn
  
  # We're not providing validation_record_fqdns since we're not creating the records ourselves
  # This will make Terraform wait for the certificate to be validated by AWS
  # before proceeding with resources that depend on the certificate

  # Set a longer timeout as DNS propagation and validation can take time
  timeouts {
    create = "60m"
  }
}