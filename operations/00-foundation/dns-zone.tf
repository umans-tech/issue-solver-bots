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