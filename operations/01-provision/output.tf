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