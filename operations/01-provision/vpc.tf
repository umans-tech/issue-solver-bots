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
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = "eu-west-3${count.index == 0 ? "a" : "b"}"

  map_public_ip_on_launch = true

  tags = {
    Name = "umans-public-subnet-${count.index}${local.environment_name_suffix}"
  }
}

# Private subnets (for Lambdas)
resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = "eu-west-3${count.index == 0 ? "a" : "b"}"

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
  count  = 0
  domain = "vpc"

  tags = {
    Name = "umans-nat-eip-${count.index}${local.environment_name_suffix}"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "nat" {
  count         = 0
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
    instance_id    = aws_instance.nat.id
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

# Data source for Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-gp2"]
  }
}

# NAT EC2 instance in public subnet
resource "aws_instance" "nat" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = "t3.nano"
  subnet_id                   = aws_subnet.public[0].id
  associate_public_ip_address = true
  source_dest_check           = false

  tags = {
    Name = "umans-nat-instance${local.environment_name_suffix}"
  }

  user_data = <<-EOF
    #!/bin/bash
    sysctl -w net.ipv4.ip_forward=1
    yum install -y iptables-services
    systemctl enable iptables
    systemctl start iptables
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    service iptables save
  EOF
}

# Elastic IP for the NAT instance (free while attached)
resource "aws_eip" "nat_instance" {
  instance = aws_instance.nat.id

  tags = {
    Name = "umans-nat-eip-instance${local.environment_name_suffix}"
  }
}