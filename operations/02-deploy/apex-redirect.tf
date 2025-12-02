data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

resource "aws_cloudfront_function" "apex_root_redirect" {
  name    = "apex-root-redirect-${local.environment_name}"
  runtime = "cloudfront-js-1.0"

  code = <<EOF
function handler(event) {
  var request = event.request;
  var host = request.headers.host.value;

  // Redirect everything on the landing host to app.<host>/home
  var targetHost = 'app.' + host.replace(/^app\./, '');
  var location = 'https://' + targetHost + '/home';

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

resource "aws_cloudfront_distribution" "apex_redirect" {
  enabled     = true
  aliases     = [local.landing_domain]
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
      function_arn = aws_cloudfront_function.apex_root_redirect.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = data.terraform_remote_state.foundation.outputs.certificate_arn_us_east_1
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

resource "aws_route53_record" "apex_redirect_alias" {
  allow_overwrite = true
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = local.landing_domain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.apex_redirect.domain_name
    zone_id                = aws_cloudfront_distribution.apex_redirect.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "apex_redirect_alias_ipv6" {
  allow_overwrite = true
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = local.landing_domain
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.apex_redirect.domain_name
    zone_id                = aws_cloudfront_distribution.apex_redirect.hosted_zone_id
    evaluate_target_health = false
  }
}
