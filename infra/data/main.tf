terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "habit-tracker-tfstate-014675907225"
    key          = "data/terraform.tfstate"
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

data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "habit-tracker-tfstate-014675907225"
    key    = "network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_db_subnet_group" "db_subnets" {
  name        = "habit-tracker-db-subnets"
  subnet_ids  = data.terraform_remote_state.network.outputs.private_subnet_ids
  description = "private subnets for app db"

  tags = {
    Name = "habit-tracker-db-subnets"
  }
}

resource "aws_db_instance" "db" {
  allocated_storage           = 20
  storage_type                = "gp3"
  publicly_accessible         = false
  db_name                     = "habit_core"
  backup_retention_period     = 1
  db_subnet_group_name        = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids      = [data.terraform_remote_state.network.outputs.db_security_group_id]
  engine                      = "postgres"
  engine_version              = "16"
  identifier                  = "habit-tracker-db"
  instance_class              = "db.t4g.micro"
  manage_master_user_password = true
  multi_az                    = false
  username                    = "habit"
  storage_encrypted           = true
  skip_final_snapshot         = true

  tags = {
    Name = "habit-tracker-db"
  }
}