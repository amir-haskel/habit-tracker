output "db_address" {
  value       = aws_db_instance.db.address
  description = "address of the db as string"
}

output "db_port" {
  value       = aws_db_instance.db.port
  description = "port of the db as number"
}

output "db_name" {
  value       = aws_db_instance.db.db_name
  description = "name of the db as string"
}

output "db_managed_secret_arn" {
  value       = aws_db_instance.db.master_user_secret[0].secret_arn
  description = "db managed secret arn as string"
}
