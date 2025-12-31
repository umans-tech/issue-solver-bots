resource "aws_cloudfront_function" "offer_redirect" {
  for_each = local.offer_redirect_domains

  name    = "offer-redirect-${each.value.subdomain}-${local.environment_name}"
  runtime = "cloudfront-js-1.0"

  code = <<EOF
function handler(event) {
  var request = event.request;
  var host = request.headers.host.value;

  var baseHost = host.replace(/^${each.value.subdomain}\./, '');
  baseHost = baseHost.replace(/^app\./, '');
  var targetHost = 'app.' + baseHost;
  var location = 'https://' + targetHost + '${each.value.path}';

  // Preserve query string if present
  if (request.querystring && Object.keys(request.querystring).length > 0) {
    var qs = Object.keys(request.querystring)
      .map(function (k) {
        var v = request.querystring[k].value;
        return v === undefined || v === '' ? k : k + '=' + v;
      })
      .join('&');
    location += '?' + qs;
  }

  return {
    statusCode: 301,
    statusDescription: 'Moved Permanently',
    headers: {
      location: { value: location }
    }
  };
}
EOF
}

resource "aws_acm_certificate" "offer_redirect" {
  for_each = local.offer_redirect_domains
  provider = aws.us_east_1

  domain_name       = each.key
  validation_method = "DNS"
}

resource "aws_route53_record" "offer_redirect_cert_validation" {
  for_each = {
    for item in flatten([
      for domain, cert in aws_acm_certificate.offer_redirect : [
        for dvo in cert.domain_validation_options : {
          key   = "${domain}:${dvo.domain_name}"
          name  = dvo.resource_record_name
          type  = dvo.resource_record_type
          value = dvo.resource_record_value
        }
      ]
    ]) : item.key => item
  }

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.value]
  ttl             = 60
}

resource "aws_acm_certificate_validation" "offer_redirect" {
  for_each = aws_acm_certificate.offer_redirect
  provider = aws.us_east_1

  certificate_arn = each.value.arn
  validation_record_fqdns = [
    for dvo in each.value.domain_validation_options :
    aws_route53_record.offer_redirect_cert_validation["${each.key}:${dvo.domain_name}"].fqdn
  ]
}

resource "aws_cloudfront_distribution" "offer_redirect" {
  for_each    = local.offer_redirect_domains
  enabled     = true
  aliases     = [each.key]
  price_class = "PriceClass_100"

  origin {
    domain_name = "invalid.example.com"
    origin_id   = "redirect-placeholder"
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    target_origin_id       = "redirect-placeholder"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    cache_policy_id        = data.aws_cloudfront_cache_policy.caching_disabled.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.offer_redirect[each.key].arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.offer_redirect[each.key].certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

resource "aws_route53_record" "offer_redirect_alias" {
  for_each = aws_cloudfront_distribution.offer_redirect

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.key
  type            = "A"

  alias {
    name                   = each.value.domain_name
    zone_id                = each.value.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "offer_redirect_alias_ipv6" {
  for_each = aws_cloudfront_distribution.offer_redirect

  allow_overwrite = true
  zone_id         = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name            = each.key
  type            = "AAAA"

  alias {
    name                   = each.value.domain_name
    zone_id                = each.value.hosted_zone_id
    evaluate_target_health = false
  }
}
