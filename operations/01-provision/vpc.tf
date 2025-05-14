# VPC pour les fonctions Lambda
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "umans-vpc${local.environment_name_suffix}"
  }
}

# Sous-réseaux publics (pour la NAT Gateway)
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

# Sous-réseaux privés (pour les Lambdas)
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

# Elastic IP pour la NAT Gateway
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "umans-nat-eip${local.environment_name_suffix}"
  }
}

# NAT Gateway
resource "aws_nat_gateway" "nat" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "umans-nat${local.environment_name_suffix}"
  }

  depends_on = [aws_internet_gateway.igw]
}

# Table de routage pour les sous-réseaux publics
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

# Table de routage pour les sous-réseaux privés
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat.id
  }

  tags = {
    Name = "umans-private-rt${local.environment_name_suffix}"
  }
}

# Association des tables de routage aux sous-réseaux publics
resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Association des tables de routage aux sous-réseaux privés
resource "aws_route_table_association" "private" {
  count          = 2
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}

# Groupe de sécurité pour les Lambdas
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