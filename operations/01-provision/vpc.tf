# VPC for Lambda functions
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "umans-vpc${local.environment_name_suffix}"
  }
}

# Public subnets (for NAT Gateway)
resource "aws_subnet" "public" {
  count             = 1
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = "eu-west-3a"

  map_public_ip_on_launch = true

  tags = {
    Name = "umans-public-subnet-${count.index}${local.environment_name_suffix}"
  }
}

# Private subnets (for Lambdas)
resource "aws_subnet" "private" {
  count             = 2
  availability_zone = "eu-west-3${count.index == 0 ? "a" : "b"}"

  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"

  tags = {
    Name = "umans-private-subnet-${count.index}${local.environment_name_suffix}"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "umans-igw${local.environment_name_suffix}"
  }
}

# Elastic IP for NAT Gateway
resource "aws_eip" "nat" {
  count  = length(aws_subnet.public)
  domain = "vpc"

  tags = {
    Name = "umans-nat-eip-${count.index}${local.environment_name_suffix}"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "nat" {
  count         = length(aws_subnet.public)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  depends_on = [aws_internet_gateway.igw]

  tags = {
    Name = "umans-nat${local.environment_name_suffix}"
  }
}

# Route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "umans-public-rt${local.environment_name_suffix}"
  }
}

# Route table for private subnets
resource "aws_route_table" "private" {
  count  = length(aws_subnet.private)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat[0].id
  }

  tags = {
    Name = "umans-private-rt-${count.index}${local.environment_name_suffix}"
  }
}

# Route table association for public subnets
resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Route table association for private subnets
resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security group for Lambdas
resource "aws_security_group" "lambda_sg" {
  name        = "lambda-sg${local.environment_name_suffix}"
  description = "Security group for Lambda functions"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "umans-lambda-sg${local.environment_name_suffix}"
  }
}