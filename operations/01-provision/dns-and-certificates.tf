# Zone hébergée Route53 pour umans.ai
resource "aws_route53_zone" "umans_ai" {
  name = "umans.ai"
}

# Certificat ACM pour *.umans.ai et umans.ai
resource "aws_acm_certificate" "umans_ai" {
  domain_name               = "umans.ai"
  subject_alternative_names = ["*.umans.ai"]
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# Enregistrements DNS pour la validation du certificat
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.umans_ai.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.umans_ai.zone_id
}

# Validation du certificat
resource "aws_acm_certificate_validation" "umans_ai" {
  certificate_arn         = aws_acm_certificate.umans_ai.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
} 