output "repository_urls" {
  value = { for k, v in aws_ecr_repository.habit : k => v.repository_url }
}
