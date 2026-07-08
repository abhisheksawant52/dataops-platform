locals {
  name_prefix = "${var.project}-${var.environment}"
}

# ---------------------------------------------------------------------------
# Networking (VPC + subnets) provided by a reusable submodule.
# ---------------------------------------------------------------------------
module "network" {
  source = "./modules/network"

  name        = local.name_prefix
  vpc_cidr    = var.vpc_cidr
  environment = var.environment
}

# ---------------------------------------------------------------------------
# S3 data lake
# ---------------------------------------------------------------------------
resource "aws_s3_bucket" "data_lake" {
  bucket = var.data_lake_bucket_name

  tags = {
    Name = "${local.name_prefix}-data-lake"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------------------------------------------------------------------------
# Glue Data Catalog database
# ---------------------------------------------------------------------------
resource "aws_glue_catalog_database" "catalog" {
  name        = replace("${local.name_prefix}_catalog", "-", "_")
  description = "Data catalog for ${var.project} (${var.environment})."
}

# ---------------------------------------------------------------------------
# IAM role assumed by pipeline execution (Glue / orchestration).
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "pipeline_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "pipeline_access" {
  statement {
    sid       = "DataLakeAccess"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.data_lake.arn, "${aws_s3_bucket.data_lake.arn}/*"]
  }

  statement {
    sid       = "CatalogAccess"
    actions   = ["glue:GetDatabase", "glue:GetTable", "glue:GetTables"]
    resources = ["*"]
  }
}

resource "aws_iam_role" "pipeline" {
  name               = "${local.name_prefix}-pipeline"
  assume_role_policy = data.aws_iam_policy_document.pipeline_assume.json
}

resource "aws_iam_role_policy" "pipeline" {
  name   = "${local.name_prefix}-pipeline-access"
  role   = aws_iam_role.pipeline.id
  policy = data.aws_iam_policy_document.pipeline_access.json
}
