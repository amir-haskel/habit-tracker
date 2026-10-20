output "topic_arn" {
  value       = aws_sns_topic.events.arn
  description = "events topic arn as string"
}

output "queue_arn" {
  value       = aws_sqs_queue.notifications.arn
  description = "notifications queue arn as string"
}

output "queue_url" {
  value       = aws_sqs_queue.notifications.id
  description = "id of the notifications queue as string"
}