terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.54"
    }
  }

  # Remote state backend. Configure per-environment with a partial backend and
  # `terraform init -backend-config=environments/<env>/backend.hcl`.
  # backend "s3" {
  #   bucket         = "my-dataops-tfstate"
  #   key            = "dataops-platform/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "dataops-tf-locks"
  #   encrypt        = true
  # }
}
