# Static blog hosting (S3 + CloudFront, private bucket with OAC and SPA rewrite)

resource "aws_s3_bucket" "blog_site" {
  bucket = "blog${local.environment_name_suffix}-site"
}

resource "aws_s3_bucket_public_access_block" "blog_site" {
  bucket                  = aws_s3_bucket.blog_site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "blog_site" {
  bucket = aws_s3_bucket.blog_site.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_cloudfront_origin_access_control" "blog" {
  name                              = "blog${local.environment_name_suffix}-oac"
  description                       = "OAC for blog static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_acm_certificate" "blog" {
  provider          = aws.us_east_1
  domain_name       = local.blog_domain
  validation_method = "DNS"
}

locals {
  blog_dvo = { for dvo in aws_acm_certificate.blog.domain_validation_options : dvo.domain_name => dvo }
}

resource "aws_route53_record" "blog_cert_validation" {
  for_each = local.blog_dvo

  name    = each.value.resource_record_name
  type    = each.value.resource_record_type
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  records = [each.value.resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "blog" {
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.blog.arn
  validation_record_fqdns = [
    for record in aws_route53_record.blog_cert_validation : record.fqdn
  ]
}

resource "aws_cloudfront_function" "blog_index_rewrite" {
  name    = "blog-${local.environment_name}-index-rewrite"
  runtime = "cloudfront-js-1.0"

  code = <<EOF_FUNCTION
function handler(event) {
  var request = event.request;
  var uri = request.uri;

  if (uri.endsWith('/')) {
    request.uri += 'index.html';
    return request;
  }

  if (!uri.includes('.')) {
    request.uri = uri + '/index.html';
  }

  return request;
}
EOF_FUNCTION
}

resource "aws_cloudfront_distribution" "blog" {
  enabled             = true
  aliases             = [local.blog_domain]
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.blog_site.bucket_regional_domain_name
    origin_id                = "blog-s3-origin"
    origin_access_control_id = aws_cloudfront_origin_access_control.blog.id
  }

  default_cache_behavior {
    target_origin_id       = "blog-s3-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6"

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.blog_index_rewrite.arn
    }
  }

  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.blog.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  price_class = "PriceClass_100"
}

resource "aws_s3_bucket_policy" "blog_site" {
  bucket = aws_s3_bucket.blog_site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontRead"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = ["s3:GetObject"]
        Resource  = ["${aws_s3_bucket.blog_site.arn}/*"]
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = "arn:aws:cloudfront::${data.aws_caller_identity.current.account_id}:distribution/${aws_cloudfront_distribution.blog.id}"
          }
        }
      }
    ]
  })
}

resource "aws_route53_record" "blog_alias" {
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = local.blog_domain
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.blog.domain_name
    zone_id                = aws_cloudfront_distribution.blog.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "blog_alias_ipv6" {
  zone_id = data.terraform_remote_state.foundation.outputs.umans_route53_zone_id
  name    = local.blog_domain
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.blog.domain_name
    zone_id                = aws_cloudfront_distribution.blog.hosted_zone_id
    evaluate_target_health = false
  }
}

