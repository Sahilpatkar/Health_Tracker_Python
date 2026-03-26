terraform {
  required_version = ">= 1.3"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# ---------------------------------------------------------------------------
# Data sources – reuse the default VPC to avoid NAT gateway costs
# ---------------------------------------------------------------------------

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------------------------------------------------------------------------
# Security group – only expose what the app needs
# ---------------------------------------------------------------------------

resource "aws_security_group" "app" {
  name_prefix = "${var.app_name}-sg-"
  description = "Health Tracker - allow app ports + SSH"
  vpc_id      = data.aws_vpc.default.id

  # SSH
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  # React frontend
  ingress {
    description = "Frontend"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI
  ingress {
    description = "API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Kafka UI (optional – remove if not needed publicly)
  ingress {
    description = "Kafka UI"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.app_name}-sg" }
}

# ---------------------------------------------------------------------------
# EBS volume for persistent data (MySQL + Kafka + uploads)
# ---------------------------------------------------------------------------

resource "aws_ebs_volume" "data" {
  availability_zone = "${var.aws_region}a"
  size              = var.ebs_size_gb
  type              = "gp3"

  tags = { Name = "${var.app_name}-data" }
}

# ---------------------------------------------------------------------------
# EC2 instance
# ---------------------------------------------------------------------------

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.app.id]
  availability_zone      = "${var.aws_region}a"

  # Use a subnet in the same AZ as the EBS volume
  subnet_id = [
    for s in data.aws_subnets.default.ids : s
  ][0]

  user_data = templatefile("${path.module}/user_data.sh", {
    ebs_device       = "/dev/xvdf"
    data_mount        = "/data"
    openai_api_key   = var.openai_api_key
    groq_api_key     = var.groq_api_key
    jwt_secret       = var.jwt_secret
    db_password      = var.db_password
    public_ip        = "" # filled at boot via instance metadata
  })

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  tags = { Name = "${var.app_name}-server" }
}

resource "aws_volume_attachment" "data" {
  device_name = "/dev/xvdf"
  volume_id   = aws_ebs_volume.data.id
  instance_id = aws_instance.app.id
}

# ---------------------------------------------------------------------------
# Elastic IP – stable public address that survives stop/start
# ---------------------------------------------------------------------------

resource "aws_eip" "app" {
  instance = aws_instance.app.id
  domain   = "vpc"

  tags = { Name = "${var.app_name}-eip" }
}
