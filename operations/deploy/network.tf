###########################
# VPC with NAT Gateway
###########################

# Create a new VPC
resource "aws_vpc" "amplify_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "amplify-vpc"
  }
}

# Create a public subnet (for NAT Gateway)
resource "aws_subnet" "amplify_public_subnet" {
  vpc_id                  = aws_vpc.amplify_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-west-3a"
  map_public_ip_on_launch = true

  tags = {
    Name = "amplify-public-subnet"
  }
}

# Create a private subnet (for your SSR Lambdas)
resource "aws_subnet" "amplify_private_subnet" {
  vpc_id            = aws_vpc.amplify_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-3a"

  tags = {
    Name = "amplify-private-subnet"
  }
}

# Create an Internet Gateway for the VPC
resource "aws_internet_gateway" "amplify_igw" {
  vpc_id = aws_vpc.amplify_vpc.id

  tags = {
    Name = "amplify-igw"
  }
}

# Create a route table for the public subnet
resource "aws_route_table" "amplify_public_rt" {
  vpc_id = aws_vpc.amplify_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.amplify_igw.id
  }

  tags = {
    Name = "amplify-public-rt"
  }
}

# Associate the public subnet with the public route table
resource "aws_route_table_association" "amplify_public_rt_assoc" {
  subnet_id      = aws_subnet.amplify_public_subnet.id
  route_table_id = aws_route_table.amplify_public_rt.id
}

# Allocate an Elastic IP for the NAT Gateway
resource "aws_eip" "amplify_nat_eip" {
  vpc = true
}

# Create the NAT Gateway in the public subnet
resource "aws_nat_gateway" "amplify_nat_gw" {
  allocation_id = aws_eip.amplify_nat_eip.id
  subnet_id     = aws_subnet.amplify_public_subnet.id

  tags = {
    Name = "amplify-nat-gw"
  }
}

# Create a route table for the private subnet that routes outbound traffic via the NAT Gateway
resource "aws_route_table" "amplify_private_rt" {
  vpc_id = aws_vpc.amplify_vpc.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.amplify_nat_gw.id
  }

  tags = {
    Name = "amplify-private-rt"
  }
}

# Associate the private subnet with its route table
resource "aws_route_table_association" "amplify_private_rt_assoc" {
  subnet_id      = aws_subnet.amplify_private_subnet.id
  route_table_id = aws_route_table.amplify_private_rt.id
}

###########################
# (Optional) Outputs
###########################
output "amplify_vpc_id" {
  description = "ID of the Amplify VPC"
  value       = aws_vpc.amplify_vpc.id
}

output "amplify_private_subnet_ids" {
  description = "IDs of the Amplify private subnets"
  value       = [aws_subnet.amplify_private_subnet.id]
}
