resource "aws_elasticache_serverless_cache" "redis_cache" {
  engine = "redis"
  name   = "redis-cache${local.environment_name_suffix}"
  
  cache_usage_limits {
    data_storage {
      maximum  = 5
      unit = "GB"
    }
    
    ecpu_per_second {
      maximum = 10000
    }
  }

  description         = "Redis cache for streaming"
  
  tags = {
    Name        = "Redis Cache"
    Environment = local.environment_name
  }
} 