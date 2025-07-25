terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

locals {
  openai_api_key = "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"
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_security_group" "sg" {
  name        = "vibewatch-sg"
  description = "Allow HTTP and SSH traffic"

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "vibewatch" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  key_name               = "vibewatch"
  vpc_security_group_ids = [aws_security_group.sg.id]

  user_data = <<-EOF
    #!/bin/bash
    set -eux

    yum update -y
    yum install -y git python3 python3-venv

    # Clone repo
    git clone https://github.com/<YOUR-GH-USER>/vibewatch.git /opt/vibewatch

    # Set up virtual environment and install deps
    python3 -m venv /opt/vibe-venv
    source /opt/vibe-venv/bin/activate
    pip install --upgrade pip
    pip install -r /opt/vibewatch/requirements.txt "uvicorn[standard]"

    # Configure OpenAI key
    echo "export OPENAI_API_KEY=${local.openai_api_key}" > /etc/profile.d/openai.sh
    export OPENAI_API_KEY=${local.openai_api_key}

    # Run the API on port 80
    cd /opt/vibewatch
    nohup uvicorn api.app:app --host 0.0.0.0 --port 80 &
  EOF

  tags = {
    Name = "vibewatch"
  }
} 