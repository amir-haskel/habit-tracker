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