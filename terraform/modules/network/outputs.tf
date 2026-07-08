output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.this.id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets."
  value       = aws_subnet.private[*].id
}

output "security_group_id" {
  description = "ID of the data-platform security group."
  value       = aws_security_group.data_platform.id
}
