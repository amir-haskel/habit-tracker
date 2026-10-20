terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket       = "habit-tracker-tfstate-014675907225"
    key          = "registry/terraform.tfstate"
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

resource "aws_ecr_repository" "habit" {
  for_each = toset(["habit-core", "notifications"])

  name                 = "habit-tracker/${each.key}"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = each.key
  }
}
