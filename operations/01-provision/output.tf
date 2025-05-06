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

output "certificate_arn" {
  value = aws_acm_certificate.umans_ai.arn
  description = "ARN of the SSL certificate for the *.umans.ai domain"
}

output "hosted_zone_id" {
  value = aws_route53_zone.umans_ai.zone_id
  description = "ID of the Route53 hosted zone for umans.ai"
}