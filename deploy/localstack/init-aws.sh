#!/bin/bash
# Runs inside LocalStack once it is ready (mounted into /etc/localstack/init/ready.d).
# Creates the same messaging resources the real AWS environment must provide —
# see docs/messaging.md for the contract. Safe to re-run: create calls are idempotent.
set -euo pipefail

REGION="${AWS_DEFAULT_REGION:-us-east-1}"
TOPIC_NAME="habit-tracker-events"
QUEUE_NAME="habit-tracker-notifications"
DLQ_NAME="habit-tracker-notifications-dlq"
ATTRS=/tmp/queue-attributes.json

TOPIC_ARN=$(awslocal sns create-topic --name "$TOPIC_NAME" --query TopicArn --output text)

# Dead-letter queue: where messages land after maxReceiveCount failed receives.
DLQ_URL=$(awslocal sqs create-queue --queue-name "$DLQ_NAME" --query QueueUrl --output text)
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url "$DLQ_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)

# Main queue (standard, long polling, redrive to the DLQ after 5 receives).
QUEUE_URL=$(awslocal sqs create-queue --queue-name "$QUEUE_NAME" --query QueueUrl --output text)
QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url "$QUEUE_URL" \
  --attribute-names QueueArn --query Attributes.QueueArn --output text)

# Queue attributes with nested-JSON values (RedrivePolicy, Policy) are easiest
# to build with python, which is present in the LocalStack image.
TOPIC_ARN="$TOPIC_ARN" QUEUE_ARN="$QUEUE_ARN" DLQ_ARN="$DLQ_ARN" python3 - > "$ATTRS" <<'PY'
import json, os

policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowSnsToSend",
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": os.environ["QUEUE_ARN"],
        "Condition": {"ArnEquals": {"aws:SourceArn": os.environ["TOPIC_ARN"]}},
    }],
}
redrive = {"deadLetterTargetArn": os.environ["DLQ_ARN"], "maxReceiveCount": "5"}
print(json.dumps({
    "VisibilityTimeout": "60",
    "ReceiveMessageWaitTimeSeconds": "20",
    "RedrivePolicy": json.dumps(redrive),
    "Policy": json.dumps(policy),
}))
PY
awslocal sqs set-queue-attributes --queue-url "$QUEUE_URL" --attributes "file://$ATTRS"

# Fan-out: topic -> queue, raw delivery, only the event types notifications handles.
# (habit.logged is published but matches no subscription.)
awslocal sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol sqs \
  --notification-endpoint "$QUEUE_ARN" \
  --attributes '{"RawMessageDelivery":"true","FilterPolicy":"{\"event_type\":[\"habit.created\",\"habit.archived\",\"streak.milestone\"]}"}'

# Marker the compose healthcheck waits for.
touch /tmp/init-complete
echo "habit-tracker messaging resources ready: $TOPIC_ARN -> $QUEUE_URL (dlq: $DLQ_URL)"
