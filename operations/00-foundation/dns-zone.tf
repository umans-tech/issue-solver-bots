// One-time DNS foundation: create Route 53 Hosted Zone for umans.ai
resource "aws_route53_zone" "umans_ai" {
  name    = "umans.ai"
  comment = "Authoritative DNS zone for umans.ai managed by Terraform"
}

// Export the hosted zone ID to use in downstream modules or layers
output "umans_route53_zone_id" {
  description = "The Route 53 Hosted Zone ID for umans.ai"
  value       = aws_route53_zone.umans_ai.zone_id
}

resource "aws_route53_record" "apex" {
  zone_id = aws_route53_zone.umans_ai.zone_id
  name    = ""
  type    = "A"
  ttl     = 300
  records = ["76.76.21.21"]    # Vercel's global edge IP for apex
}

resource "aws_route53_record" "wildcard" {
  zone_id = aws_route53_zone.umans_ai.zone_id
  name    = "*"
  type    = "A"
  ttl     = 300
  records = ["76.76.21.21"]    # covers app.umans.ai and any other subdomain
}

output "route53_name_servers" {
  value       = aws_route53_zone.umans_ai.name_servers
  description = "The NS records to configure at your registrar"
}

resource "aws_acm_certificate" "umans" {
  domain_name               = "umans.ai"
  subject_alternative_names = ["*.umans.ai"]
  validation_method         = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  allow_overwrite = true
  for_each = {
    for dvo in aws_acm_certificate.umans.domain_validation_options :
    dvo.domain_name => dvo
  }
  zone_id = aws_route53_zone.umans_ai.zone_id
  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  records = [each.value.resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "umans" {
  certificate_arn         = aws_acm_certificate.umans.arn
  validation_record_fqdns = [for rec in aws_route53_record.cert_validation : rec.fqdn]
}

output "certificate_arn" {
  description = "ARN of ACM certificate for umans.ai and *.umans.ai"
  value       = aws_acm_certificate.umans.arn
}

provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
}

resource "aws_acm_certificate" "umans_us_east_1" {
  provider                  = aws.us_east_1
  domain_name               = "umans.ai"
  subject_alternative_names = ["*.umans.ai"]
  validation_method         = "DNS"
}

resource "aws_route53_record" "cert_validation_us_east_1" {
  for_each = {
    for dvo in aws_acm_certificate.umans_us_east_1.domain_validation_options :
    dvo.domain_name => dvo
  }
  allow_overwrite = true
  zone_id         = aws_route53_zone.umans_ai.zone_id
  name            = each.value.resource_record_name
  type            = each.value.resource_record_type
  records         = [each.value.resource_record_value]
  ttl             = 60
}

resource "aws_acm_certificate_validation" "umans_us_east_1" {
  provider                = aws.us_east_1
  certificate_arn         = aws_acm_certificate.umans_us_east_1.arn
  validation_record_fqdns = [for rec in aws_route53_record.cert_validation_us_east_1 : rec.fqdn]
}

output "certificate_arn_us_east_1" {
  description = "ARN of validated ACM certificate in us-east-1 for API Gateway v2"
  value       = aws_acm_certificate_validation.umans_us_east_1.certificate_arn
}