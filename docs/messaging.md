# Messaging contract (SNS + SQS)

This is the contract between the application and AWS. The app creates **no**
messaging resources itself: whoever provisions the environment (Terraform) must
create everything below, with these exact names. The local stack mirrors it in
[`deploy/localstack/init-aws.sh`](../deploy/localstack/init-aws.sh) — treat that
script as an executable reference.

```
habit-core --publish--> SNS topic habit-tracker-events
                          |  subscription: raw delivery + filter on event_type
                          v
                        SQS queue habit-tracker-notifications --(5 failed receives)--> SQS DLQ habit-tracker-notifications-dlq
                          ^
                          |  long-poll receive, delete after handler success
                        notifications
```

## Resources

| Resource | Type | Name |
|---|---|---|
| Event topic | SNS standard topic | `habit-tracker-events` |
| Notifications queue | SQS **standard** queue | `habit-tracker-notifications` |
| Dead-letter queue | SQS **standard** queue | `habit-tracker-notifications-dlq` |

Standard queues and topics only — not FIFO. Delivery is at-least-once and
unordered; handlers must tolerate duplicates (events carry no id today).

## Message format

habit-core publishes each event with:

- **Message body:** the event as JSON (`event.model_dump_json()`), e.g.
  `{"event_type":"streak.milestone","occurred_at":"...","habit_id":4,"streak_length":7}`.
  The models live in `libs/events/src/habit_events/events.py`.
- **Message attribute** `event_type` (DataType `String`): the same value as the
  body's `event_type` field. SNS filter policies match on attributes, not the body.

Event types: `habit.created`, `habit.archived`, `habit.logged`, `streak.milestone`.

## SNS subscription (topic -> notifications queue)

| Setting | Value |
|---|---|
| Protocol | `sqs`, endpoint = ARN of `habit-tracker-notifications` |
| `RawMessageDelivery` | `true` — the SQS body is the event JSON itself, and the `event_type` attribute arrives as an SQS message attribute. Without it the body is an SNS envelope and the consumer cannot decode it. |
| `FilterPolicy` | `{"event_type": ["habit.created", "habit.archived", "streak.milestone"]}` |
| `FilterPolicyScope` | `MessageAttributes` (the default) |

`habit.logged` is published but matches no subscription, so it is dropped by SNS.
When a new service needs it, add a new queue + subscription; do not widen this one.
If notifications starts handling another event type, extend the filter policy
(and `EVENT_TYPES` in `services/notifications/src/notifications/handlers.py`).

## Queue settings

`habit-tracker-notifications`:

| Setting | Recommended | Why |
|---|---|---|
| `ReceiveMessageWaitTimeSeconds` | `20` | Long polling by default; the consumer also asks for `WaitTimeSeconds=20`. Fewer empty receives, lower cost and latency. |
| `VisibilityTimeout` | `60` (seconds) | Must comfortably exceed the time to handle one batch: the consumer handles up to 10 messages sequentially, each a short DB write (well under a second), so 60s is generous. If a batch outlives the timeout, messages reappear while still being processed and get handled twice. Raise it if handlers ever become slow. |
| `RedrivePolicy` | `{"deadLetterTargetArn": "<dlq arn>", "maxReceiveCount": 5}` | A message whose handler keeps failing (or that cannot be decoded) is **not deleted**; after 5 receives SQS moves it to the DLQ. |
| `MessageRetentionPeriod` | default (4 days) or longer | Events buffer here while notifications is down. |
| `Policy` | see below | Lets the topic deliver into the queue. |
| Encryption | SSE-SQS (`SqsManagedSseEnabled=true`), or KMS | If a customer-managed KMS key is used, the key policy must allow `sns.amazonaws.com` to `kms:GenerateDataKey*` and `kms:Decrypt`, and the topic must be encrypted with a key SNS can use too. |

`habit-tracker-notifications-dlq`: retention longer than the main queue
(e.g. 14 days) so failures can be inspected and redriven; add a CloudWatch alarm
on `ApproximateNumberOfMessagesVisible > 0`.

### Queue policy (SNS -> SQS)

Attached to `habit-tracker-notifications`; without it the subscription is created
but every delivery is silently denied:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowSnsToSend",
    "Effect": "Allow",
    "Principal": {"Service": "sns.amazonaws.com"},
    "Action": "sqs:SendMessage",
    "Resource": "<ARN of habit-tracker-notifications>",
    "Condition": {"ArnEquals": {"aws:SourceArn": "<ARN of habit-tracker-events>"}}
  }]
}
```

## IAM (task roles; no keys in code or config)

Both services use boto3's default credential chain; on ECS the **task role**
supplies credentials. Do not set `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` there.

| Service | Action(s) | Resource |
|---|---|---|
| habit-core | `sns:Publish` | ARN of `habit-tracker-events` |
| notifications | `sqs:ReceiveMessage`, `sqs:DeleteMessage`, `sqs:ChangeMessageVisibility`, `sqs:GetQueueAttributes` | ARN of `habit-tracker-notifications` |

The DLQ needs no service permissions: SQS moves messages there itself.
(If the notifications queue uses a customer-managed KMS key, habit-core also
needs `kms:GenerateDataKey*`/`kms:Decrypt` on the topic's key, and notifications
`kms:Decrypt` on the queue's key.)

## Environment variables

Settings are read by pydantic-settings (case-insensitive), plus boto3's own
standard variables.

**habit-core**

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./habit_core.db` | SQLAlchemy URL (Postgres/RDS on AWS). |
| `EVENT_BUS` | `memory` | `aws` to publish to SNS; `memory` keeps events in-process. The Docker image sets `aws`. |
| `SNS_TOPIC_ARN` | *(empty)* | ARN of `habit-tracker-events`. Required when `EVENT_BUS=aws`; startup fails without it. |
| `AWS_REGION` | *(unset)* | Region for the SNS client. Falls back to boto3's chain (`AWS_DEFAULT_REGION`, ECS metadata) if unset. |
| `AWS_ENDPOINT_URL` | *(unset)* | boto3 standard variable; set only for LocalStack. Leave unset on AWS. |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN` | *(unset)* | boto3 credential chain. LocalStack/compose only (`test`/`test`). |

**notifications**

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./notifications.db` | SQLAlchemy URL. |
| `EVENT_BUS` | `memory` | `aws` starts the embedded SQS consumer thread at startup. The Docker image sets `aws`. |
| `SQS_QUEUE_URL` | *(empty)* | URL (not ARN) of `habit-tracker-notifications`. Required when `EVENT_BUS=aws`; startup fails without it. |
| `AWS_REGION` | *(unset)* | As above, for the SQS client. |
| `AWS_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | *(unset)* | As above. |

## Consumer behaviour worth knowing when sizing things

- Long poll `WaitTimeSeconds=20`, `MaxNumberOfMessages=10`; messages in a batch are
  handled sequentially, and each is deleted right after its own handler succeeds.
- A handler exception is logged and the message left undeleted (redelivered after
  the visibility timeout, DLQ after 5 receives). An undecodable message (unknown
  `event_type`, bad JSON) is treated the same way.
- SQS/network errors (throttling, missing queue, expired credentials, endpoint
  unreachable) are logged and retried with exponential backoff, 3s doubling up
  to 60s; the loop never exits. The queue not existing yet is therefore a
  retry, not a crash — but the service will not process anything until it does.
- The consumer runs inside the notifications API process, so every task of that
  service polls the same queue (competing consumers). Duplicates are possible
  by design (at-least-once).
