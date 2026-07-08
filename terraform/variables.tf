variable "region" {
  description = "AWS region to deploy the data platform into."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "project" {
  description = "Project name used for tagging and resource naming."
  type        = string
  default     = "dataops-platform"
}

variable "data_lake_bucket_name" {
  description = "Globally unique name for the S3 data-lake bucket."
  type        = string
}

variable "warehouse_node_type" {
  description = "Instance/node type for the analytics warehouse."
  type        = string
  default     = "dc2.large"
}

variable "vpc_cidr" {
  description = "CIDR block for the data-platform VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "tags" {
  description = "Additional tags merged into the provider default_tags."
  type        = map(string)
  default     = {}
}
