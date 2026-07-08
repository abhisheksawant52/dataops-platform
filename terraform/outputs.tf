output "data_lake_bucket_name" {
  description = "Name of the S3 data-lake bucket."
  value       = aws_s3_bucket.data_lake.id
}

output "data_lake_bucket_arn" {
  description = "ARN of the S3 data-lake bucket."
  value       = aws_s3_bucket.data_lake.arn
}

output "glue_catalog_database" {
  description = "Name of the Glue catalog database."
  value       = aws_glue_catalog_database.catalog.name
}

output "pipeline_role_arn" {
  description = "ARN of the IAM role assumed by data pipelines."
  value       = aws_iam_role.pipeline.arn
}

output "vpc_id" {
  description = "ID of the data-platform VPC."
  value       = module.network.vpc_id
}
