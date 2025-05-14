output "transaction_pooler_connection_string" {
  value = format(
    "postgresql://postgres.%s:%s@aws-0-%s.pooler.supabase.com:%s/postgres?sslmode=require&supa=base-pooler.x",
    supabase_project.conversational_ui.id,
    random_password.conversational_ui_db_password.result,
    supabase_project.conversational_ui.region,
    var.pooler_port
  )
  sensitive = true
}

output "transaction_pooler_jdbc_connection_string" {
  description = "JDBC connection string for transaction pooler"
  value = format(
    "jdbc:postgresql://aws-0-%s.pooler.supabase.com:%s/postgres?user=postgres.%s&password=%s",
    supabase_project.conversational_ui.region,
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

output "blob_bucket_name" {
  value = aws_s3_bucket.conversational_ui_blob_storage.bucket
}

output "blob_region" {
  value = "eu-west-3"
}

output "blob_access_key_id" {
  value = aws_iam_access_key.conversational_ui_blob_access_key.id
  sensitive = true
}

output "blob_secret_access_key" {
  value = aws_iam_access_key.conversational_ui_blob_access_key.secret
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