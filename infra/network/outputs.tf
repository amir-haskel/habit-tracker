output "vpc_id" {
  value       = aws_vpc.main.id
  description = "id of the apps vpc as string"
}

output "public_subnet_ids" {
  value       = [aws_subnet.public_a.id, aws_subnet.public_b.id]
  description = "list of ids as strings of public subnets"
}

output "private_subnet_ids" {
  value       = [aws_subnet.private_a.id, aws_subnet.private_b.id]
  description = "list of ids  as strings of private subnets"
}

output "app_security_group_id" {
  value       = aws_security_group.app.id
  description = "id of apps security group as string"
}

output "db_security_group_id" {
  value       = aws_security_group.db.id
  description = "id of databases security group as string"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "id of the load balancer security group"
}

output "gateway_security_group_id" {
  value       = aws_security_group.gateway.id
  description = "id of the gateway security group"
}