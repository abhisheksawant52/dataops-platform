variable "name" {
  description = "Name prefix for networking resources."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "environment" {
  description = "Deployment environment."
  type        = string
  default     = "dev"
}

variable "subnet_count" {
  description = "Number of private subnets to create."
  type        = number
  default     = 2
}
