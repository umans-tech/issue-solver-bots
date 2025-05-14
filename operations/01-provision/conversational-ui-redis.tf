resource "aws_elasticache_serverless_cache" "conversational_ui_redis" {
  engine = "redis"
  name   = "conversational-ui-redis${local.environment_name_suffix}"
  
  cache_usage_limits {
    data_storage {
      maximum  = 5
      unit = "GB"
    }
    
    ecpu_per_second {
      maximum = 10000
    }
  }

  security_group_ids = [aws_security_group.redis_sg.id]
  subnet_ids         = aws_subnet.private[*].id

  tags = {
    Name        = "Conversational UI Redis"
    Environment = local.environment_name
  }
}

resource "aws_security_group" "redis_sg" {
  name        = "redis-sg${local.environment_name_suffix}"
  description = "Security group for Redis ElastiCache Serverless"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    security_groups = [aws_security_group.lambda_sg.id]
    description = "Allow Redis traffic from Lambda"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name        = "Redis Security Group"
    Environment = local.environment_name
  }
} 