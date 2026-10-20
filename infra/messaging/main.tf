terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "habit-tracker-tfstate-014675907225"
    key          = "messaging/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project   = "habit-tracker"
      ManagedBy = "terraform"
    }
  }
}


resource "aws_sns_topic" "events" {
  name = "habit-tracker-events"

  tags = {
    Name = "habit-tracker-events"
  }
}

resource "aws_sqs_queue" "dlq" {
  name                      = "habit-tracker-notifications-dlq"
  message_retention_seconds = 1209600
  sqs_managed_sse_enabled   = true

  tags = {
    Name = "habit-tracker-notifications-dlq"
  }
}

resource "aws_sqs_queue" "notifications" {
  name                       = "habit-tracker-notifications"
  visibility_timeout_seconds = 60
  receive_wait_time_seconds  = 20
  sqs_managed_sse_enabled    = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 5
  })

  tags = {
    Name = "habit-tracker-notifications"
  }
}

data "aws_iam_policy_document" "notifications_queue" {
  statement {
    sid       = "AllowSnsToSend"
    effect    = "Allow"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.notifications.arn]

    principals {
      type        = "Service"
      identifiers = ["sns.amazonaws.com"]
    }

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [aws_sns_topic.events.arn]
    }
  }
}

resource "aws_sqs_queue_policy" "notifications" {
  queue_url = aws_sqs_queue.notifications.id
  policy    = data.aws_iam_policy_document.notifications_queue.json
}

resource "aws_sns_topic_subscription" "events_to_notifications" {
  topic_arn            = aws_sns_topic.events.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.notifications.arn
  raw_message_delivery = "true"
  filter_policy = jsonencode({
    "event_type" : ["habit.created", "habit.archived", "streak.milestone"]
  })
}

