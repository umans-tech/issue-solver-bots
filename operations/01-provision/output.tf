data "supabase_pooler" "db" {
  project_ref = supabase_project.conversational_ui.id
}

locals {
  pooler_urls = try(data.supabase_pooler.db.url, {})
  pooler_host = regex("^[^@]+@([^:]+):.*$", values(local.pooler_urls)[0])[0]
}

output "transaction_pooler_connection_string" {
  value = format(
    "postgresql://postgres.%s:%s@%s:%s/postgres?sslmode=require&supa=base-pooler.x",
    supabase_project.conversational_ui.id,
    random_password.conversational_ui_db_password.result,
    local.pooler_host,
    var.pooler_port
  )
  sensitive = true
}

output "direct_database_connection_string" {
  description = "Direct PostgreSQL connection string for migrations (bypassing PgBouncer)"
  value = format(
    "postgresql+asyncpg://postgres:%s@db.%s.supabase.co:5432/postgres?ssl=true",
    random_password.conversational_ui_db_password.result,
    supabase_project.conversational_ui.id
  )
  sensitive = true
}

output "session_pooler_connection_string" {
  description = "Session Pooler PostgreSQL connection string for migrations (alternative to direct connection)"
  value = format(
    "postgresql+asyncpg://postgres.%s:%s@%s:5432/postgres",
    supabase_project.conversational_ui.id,
    random_password.conversational_ui_db_password.result,
    local.pooler_host
  )
  sensitive = true
}

output "transaction_pooler_jdbc_connection_string" {
  description = "JDBC connection string for transaction pooler"
  value = format(
    "jdbc:postgresql://%s:%s/postgres?user=postgres.%s&password=%s",
    local.pooler_host,
    var.pooler_port,
    supabase_project.conversational_ui.id,
    random_password.conversational_ui_db_password.result
  )
  sensitive = true
}

output "redis_connection_string" {
  description = "Redis connection string for the Conversational UI"
  value       = "rediss://${aws_elasticache_serverless_cache.conversational_ui_redis.endpoint[0].address}:6379"
  sensitive   = true
}

# --- Blog static site (moved from deploy layer) ---
output "blog_domain" {
  value       = local.blog_domain
  description = "Blog domain name (e.g., blog.umans.ai or blog.pr-xxx.umans.ai)"
}

output "blog_url" {
  value       = "https://${local.blog_domain}"
  description = "Public URL of the blog CloudFront distribution"
}

output "blog_bucket_name" {
  value       = aws_s3_bucket.blog_site.bucket
  description = "S3 bucket that hosts the static blog"
}

output "blog_distribution_id" {
  value       = aws_cloudfront_distribution.blog.id
  description = "CloudFront distribution ID for the blog (used for invalidations)"
}

output "blog_oac_id" {
  value       = aws_cloudfront_origin_access_control.blog.id
  description = "Origin Access Control ID attached to the blog bucket"
}

output "blog_certificate_arn" {
  value       = aws_acm_certificate.blog.arn
  description = "ACM certificate ARN (us-east-1) for the blog domain"
}

output "blob_bucket_name" {
  value = aws_s3_bucket.knowledge_blob_storage.bucket
}

output "blob_region" {
  value = "eu-west-3"
}

output "blob_access_key_id" {
  value     = aws_iam_access_key.knowledge_blob_access_key.id
  sensitive = true
}

output "blob_secret_access_key" {
  value     = aws_iam_access_key.knowledge_blob_access_key.secret
  sensitive = true
}

output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "The IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "lambda_security_group_id" {
  description = "The ID of the Lambda security group"
  value       = aws_security_group.lambda_sg.id
}
