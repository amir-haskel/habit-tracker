terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "habit-tracker-tfstate-014675907225"
    key          = "app/terraform.tfstate"
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


data "terraform_remote_state" "messaging" {
  backend = "s3"

  config = {
    bucket = "habit-tracker-tfstate-014675907225"
    key    = "messaging/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "registry" {
  backend = "s3"

  config = {
    bucket = "habit-tracker-tfstate-014675907225"
    key    = "registry/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket = "habit-tracker-tfstate-014675907225"
    key    = "data/terraform.tfstate"
    region = "us-east-1"
  }
}

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "habit-tracker-tfstate-014675907225"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}


data "aws_iam_policy_document" "ecs_exec" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_exec" {
  name               = "habit-tracker-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_exec.json

  tags = {
    Name = "habit-tracker-ecs-execution"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_task" {
  role       = aws_iam_role.ecs_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "habit_core_task" {
  statement {
    effect    = "Allow"
    actions   = ["sns:Publish"]
    resources = [data.terraform_remote_state.messaging.outputs.topic_arn]
  }
}

resource "aws_iam_role" "habit_core_task" {
  name               = "habit-tracker-habit-core-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_exec.json

  tags = {
    Name = "habit-tracker-habit-core-task"
  }
}

resource "aws_iam_role_policy" "habit_core_task" {
  name   = "publish-to-events-topic"
  role   = aws_iam_role.habit_core_task.name
  policy = data.aws_iam_policy_document.habit_core_task.json
}

data "aws_iam_policy_document" "notifications_task" {
  statement {
    effect = "Allow"
    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:ChangeMessageVisibility",
      "sqs:GetQueueAttributes",
    ]
    resources = [data.terraform_remote_state.messaging.outputs.queue_arn]
  }
}

resource "aws_iam_role" "notifications_task" {
  name               = "habit-tracker-notifications-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_exec.json

  tags = {
    Name = "habit-tracker-notifications-task"
  }
}

resource "aws_iam_role_policy" "notifications_task" {
  name   = "consume-notifications-queue"
  role   = aws_iam_role.notifications_task.name
  policy = data.aws_iam_policy_document.notifications_task.json
}

resource "aws_cloudwatch_log_group" "services" {
  for_each = toset(["habit-core", "notifications", "gateway"])

  name              = "/ecs/habit-tracker/${each.key}"
  retention_in_days = 7

  tags = {
    Name = each.key
  }
}

resource "aws_ecs_cluster" "main" {
  name = "habit-tracker"

  setting {
    name  = "containerInsights"
    value = "disabled"
  }

  tags = {
    Name = "habit-tracker"
  }
}

locals {
  region = "us-east-1"
  image_versions = {
    "habit-core"    = "v2"
    "notifications" = "v3"
    "gateway"       = "v1"
  }
  db_secret_arn = data.terraform_remote_state.data.outputs.db_managed_secret_arn

  db_environment = [
    { name = "DB_HOST", value = data.terraform_remote_state.data.outputs.db_address },
    { name = "DB_PORT", value = tostring(data.terraform_remote_state.data.outputs.db_port) },
    { name = "DB_SSLMODE", value = "require" },
  ]

  db_secrets = [
    { name = "DB_USER", valueFrom = "${local.db_secret_arn}:username::" },
    { name = "DB_PASSWORD", valueFrom = "${local.db_secret_arn}:password::" },
  ]
}

data "aws_iam_policy_document" "ecs_exec_secrets" {
  statement {
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [local.db_secret_arn]
  }
}

resource "aws_iam_role_policy" "ecs_exec_secrets" {
  name   = "read-db-secret"
  role   = aws_iam_role.ecs_exec.name
  policy = data.aws_iam_policy_document.ecs_exec_secrets.json
}

resource "aws_ecs_task_definition" "habit_core" {
  family                   = "habit-tracker-habit-core"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_exec.arn
  task_role_arn            = aws_iam_role.habit_core_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "habit-core"
      image     = "${data.terraform_remote_state.registry.outputs.repository_urls["habit-core"]}:${local.image_versions["habit-core"]}"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      environment = concat(local.db_environment, [
        { name = "DB_NAME", value = data.terraform_remote_state.data.outputs.db_name },
        { name = "EVENT_BUS", value = "aws" },
        { name = "SNS_TOPIC_ARN", value = data.terraform_remote_state.messaging.outputs.topic_arn },
        { name = "AWS_REGION", value = local.region },
      ])

      secrets = local.db_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.services["habit-core"].name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "habit-tracker-habit-core"
  }
}

resource "aws_ecs_task_definition" "notifications" {
  family                   = "habit-tracker-notifications"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_exec.arn
  task_role_arn            = aws_iam_role.notifications_task.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "notifications"
      image     = "${data.terraform_remote_state.registry.outputs.repository_urls["notifications"]}:${local.image_versions["notifications"]}"
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      environment = concat(local.db_environment, [
        { name = "DB_NAME", value = "notifications" },
        { name = "EVENT_BUS", value = "aws" },
        { name = "CREATE_DATABASE_ON_STARTUP", value = "true" },
        { name = "SQS_QUEUE_URL", value = data.terraform_remote_state.messaging.outputs.queue_url },
        { name = "AWS_REGION", value = local.region },
      ])

      secrets = local.db_secrets

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.services["notifications"].name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "habit-tracker-notifications"
  }
}

resource "aws_ecs_task_definition" "gateway" {
  family                   = "habit-tracker-gateway"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_exec.arn

  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = "gateway"
      image     = "${data.terraform_remote_state.registry.outputs.repository_urls["gateway"]}:${local.image_versions["gateway"]}"
      essential = true

      portMappings = [
        { containerPort = 80, protocol = "tcp" }
      ]

      environment = [
        { name = "DNS_RESOLVER", value = "10.0.0.2" },
        { name = "HABIT_CORE_UPSTREAM", value = "habit-core.habit.local:8000" },
        { name = "NOTIFICATIONS_UPSTREAM", value = "notifications.habit.local:8000" },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.services["gateway"].name
          "awslogs-region"        = local.region
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "habit-tracker-gateway"
  }
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "habit-tracker-nat"
  }
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = data.terraform_remote_state.network.outputs.public_subnet_ids[0]

  tags = {
    Name = "habit-tracker-nat"
  }
}

resource "aws_route_table" "private" {
  vpc_id = data.terraform_remote_state.network.outputs.vpc_id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "habit-tracker-private-rt"
  }
}

resource "aws_route_table_association" "private" {
  for_each = toset(data.terraform_remote_state.network.outputs.private_subnet_ids)

  subnet_id      = each.value
  route_table_id = aws_route_table.private.id
}

resource "aws_ecs_service" "habit_core" {
  name            = "habit-tracker-habit-core"
  cluster         = aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.habit_core.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.terraform_remote_state.network.outputs.private_subnet_ids
    security_groups  = [data.terraform_remote_state.network.outputs.app_security_group_id]
    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.services["habit-core"].arn
  }

  depends_on = [aws_route_table_association.private]

  tags = {
    Name = "habit-tracker-habit-core"
  }
}

resource "aws_ecs_service" "notifications" {
  name            = "habit-tracker-notifications"
  cluster         = aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.notifications.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.terraform_remote_state.network.outputs.private_subnet_ids
    security_groups  = [data.terraform_remote_state.network.outputs.app_security_group_id]
    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  service_registries {
    registry_arn = aws_service_discovery_service.services["notifications"].arn
  }

  depends_on = [aws_route_table_association.private]

  tags = {
    Name = "habit-tracker-notifications"
  }
}

resource "aws_ecs_service" "gateway" {
  name            = "habit-tracker-gateway"
  cluster         = aws_ecs_cluster.main.arn
  task_definition = aws_ecs_task_definition.gateway.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.terraform_remote_state.network.outputs.private_subnet_ids
    security_groups  = [data.terraform_remote_state.network.outputs.gateway_security_group_id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.gateway.arn
    container_name   = "gateway"
    container_port   = 80
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.http, aws_route_table_association.private]

  tags = {
    Name = "habit-tracker-gateway"
  }
}

resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "habit.local"
  vpc  = data.terraform_remote_state.network.outputs.vpc_id

  tags = {
    Name = "habit.local"
  }
}

resource "aws_service_discovery_service" "services" {
  for_each = toset(["habit-core", "notifications"])

  name = each.key

  dns_config {
    namespace_id   = aws_service_discovery_private_dns_namespace.main.id
    routing_policy = "MULTIVALUE"

    dns_records {
      type = "A"
      ttl  = 10
    }
  }

  tags = {
    Name = each.key
  }
}

resource "aws_lb" "main" {
  name               = "habit-tracker"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [data.terraform_remote_state.network.outputs.alb_security_group_id]
  subnets            = data.terraform_remote_state.network.outputs.public_subnet_ids

  tags = {
    Name = "habit-tracker"
  }
}

resource "aws_lb_target_group" "gateway" {
  name                 = "habit-tracker-gateway"
  port                 = 80
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = data.terraform_remote_state.network.outputs.vpc_id
  deregistration_delay = 30

  health_check {
    path                = "/healthz"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "habit-tracker-gateway"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }
}