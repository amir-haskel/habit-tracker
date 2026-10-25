resource "aws_security_group" "app" {
  name        = "habit-tracker-app-sg"
  description = "Application containers"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "habit-tracker-app-sg"
  }
}

resource "aws_security_group" "db" {
  name        = "habit-tracker-db-sg"
  description = "Postgres database"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "habit-tracker-db-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "allow_db_connection" {
  security_group_id            = aws_security_group.db.id
  referenced_security_group_id = aws_security_group.app.id
  from_port                    = 5432
  ip_protocol                  = "tcp"
  to_port                      = 5432
}

resource "aws_vpc_security_group_egress_rule" "app_allow_all" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_security_group" "alb" {
  name        = "habit-tracker-alb-sg"
  description = "Public load balancer"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "habit-tracker-alb-sg"
  }
}

resource "aws_security_group" "gateway" {
  name        = "habit-tracker-gateway-sg"
  description = "nginx gateway"
  vpc_id      = aws_vpc.main.id

  tags = {
    Name = "habit-tracker-gateway-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = var.allowed_cidr
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "alb_to_gateway" {
  security_group_id            = aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.gateway.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

resource "aws_vpc_security_group_ingress_rule" "gateway_from_alb" {
  security_group_id            = aws_security_group.gateway.id
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 80
  to_port                      = 80
}

resource "aws_vpc_security_group_egress_rule" "gateway_allow_all" {
  security_group_id = aws_security_group.gateway.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "app_from_gateway" {
  security_group_id            = aws_security_group.app.id
  referenced_security_group_id = aws_security_group.gateway.id
  ip_protocol                  = "tcp"
  from_port                    = 8000
  to_port                      = 8000
}