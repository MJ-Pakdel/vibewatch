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

resource "aws_iam_role" "vibewatch_role" {
  name = "vibewatch-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "vibewatch_ssm_policy" {
  name = "vibewatch-ssm-policy"
  role = aws_iam_role.vibewatch_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:*:*:parameter/vibewatch/*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "vibewatch_cloudwatch_policy" {
  name = "vibewatch-cloudwatch-policy"
  role = aws_iam_role.vibewatch_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:*:*:log-group:/aws/vibewatch/*",
          "arn:aws:logs:*:*:log-group:/aws/vibewatch/*:log-stream:*"
        ]
      }
    ]
  })
}

resource "aws_iam_instance_profile" "vibewatch_profile" {
  name = "vibewatch-profile"
  role = aws_iam_role.vibewatch_role.name
}

resource "aws_instance" "vibewatch" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.medium"
  key_name               = "debug-vibewatch"
  vpc_security_group_ids = [aws_security_group.sg.id]
  iam_instance_profile   = aws_iam_instance_profile.vibewatch_profile.name

  user_data = <<-EOF
    #!/bin/bash
    set -e
    
    # Redirect all output to a log file
    exec > >(tee /var/log/user-data.log)
    exec 2>&1
    
    echo "=== Starting user-data script at $(date) ==="
    
    echo "=== Updating system ==="
    yum update -y
    
    echo "=== Installing packages ==="
    yum install -y git python3 amazon-cloudwatch-agent
    
    echo "=== Cloning repository ==="
    git clone https://github.com/MJ-Pakdel/vibewatch.git /opt/vibewatch
    ls -la /opt/vibewatch/
    
    echo "=== Setting up virtual environment ==="
    python3 -m venv /opt/vibe-venv
    source /opt/vibe-venv/bin/activate
    
    echo "=== Upgrading pip ==="
    pip install --upgrade pip
    
    echo "=== Installing requirements ==="
    cd /opt/vibewatch
    cat requirements.txt
    pip install -r requirements.txt "uvicorn[standard]"
    
    echo "=== Fetching OpenAI key from Parameter Store ==="
    OPENAI_API_KEY=$(aws ssm get-parameter --name "/vibewatch/openai-api-key" --with-decryption --query Parameter.Value --output text --region us-east-1)
    echo "export OPENAI_API_KEY=$OPENAI_API_KEY" > /etc/profile.d/openai.sh
    echo "export OPENAI_API_KEY=$OPENAI_API_KEY" >> /etc/environment
    export OPENAI_API_KEY=$OPENAI_API_KEY
    echo "OpenAI key configured successfully"
    
    echo "=== Configuring CloudWatch Agent ==="
    cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'CW_CONFIG'
    {
      "agent": {
        "metrics_collection_interval": 60,
        "logfile": "/var/log/amazon-cloudwatch-agent.log"
      },
      "logs": {
        "logs_collected": {
          "files": {
            "collect_list": [
              {
                "file_path": "/var/log/user-data.log",
                "log_group_name": "/aws/vibewatch/user-data",
                "log_stream_name": "{instance_id}",
                "timezone": "UTC"
              },
              {
                "file_path": "/var/log/uvicorn.log",
                "log_group_name": "/aws/vibewatch/uvicorn",
                "log_stream_name": "{instance_id}",
                "timezone": "UTC"
              }
            ]
          }
        }
      }
    }
    CW_CONFIG
    /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json -s
    echo "CloudWatch Agent started"
    
    echo "=== Creating startup script ==="
    cat > /opt/start_vibewatch.sh << 'SCRIPT_EOF'
    #!/bin/bash
    cd /opt/vibewatch
    source /opt/vibe-venv/bin/activate
    export OPENAI_API_KEY=$(aws ssm get-parameter --name "/vibewatch/openai-api-key" --with-decryption --query Parameter.Value --output text --region us-east-1)
    exec uvicorn api.app:app --host 0.0.0.0 --port 80
    SCRIPT_EOF
    chmod +x /opt/start_vibewatch.sh
    
    echo "=== Testing FastAPI app ==="
    python -c "from api.app import app; print('App imported successfully')"
    
    echo "=== Starting uvicorn server ==="
    nohup /opt/start_vibewatch.sh > /var/log/uvicorn.log 2>&1 &
    
    echo "=== Waiting for server to start ==="
    sleep 10
    
    echo "=== Testing server locally ==="
    curl -f http://localhost:80 || echo "Local server test failed"
    
    echo "=== User-data script completed at $(date) ==="
    echo "=== Check /var/log/uvicorn.log for server logs ==="
  EOF

  tags = {
    Name = "vibewatch"
  }
}