# Optionally, fetch the default VPC and its subnets (or reference your own VPC)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

resource "aws_db_subnet_group" "rds_postgres_subnet_group" {
  name        = "rds-postgres-subnet-group-${local.environment_name}"
  subnet_ids  = data.aws_subnets.default.ids
  description = "Subnet group for RDS PostgreSQL"
}

# Create a security group for PostgreSQL allowing inbound access on port 5432.
# NOTE: For production, restrict the CIDR blocks appropriately.
resource "aws_security_group" "rds_pg_security_group" {
  name        = "rds-pg-sg-${local.environment_name}"
  description = "Allow inbound PostgreSQL traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "Allow PostgreSQL"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create the PostgreSQL RDS instance.
resource "aws_db_instance" "postgres_rds" {
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version = "17.2"       # Adjust as needed.
  instance_class = "db.t3.micro"  # Choose an instance size suitable for your workload.
  db_name = "umansuidb"   # The database name.
  username             = "postgres"
  password             = var.rds_db_password
  skip_final_snapshot  = true
  publicly_accessible  = true

  vpc_security_group_ids = [aws_security_group.rds_pg_security_group.id]
  db_subnet_group_name = aws_db_subnet_group.rds_postgres_subnet_group.name
}

