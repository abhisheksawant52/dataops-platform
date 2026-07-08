# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-08

### Added

- `dataops` Python package: pipeline orchestration (`networkx` DAG runner),
  a data-quality rules engine (`not_null`, `unique`, `in_range`, `regex_match`,
  `row_count_between`), and a `networkx`-backed lineage graph.
- FastAPI service with `/health`, `/ready`, `/metrics`, `/pipelines/run`,
  `/quality/validate`, and `/lineage/{dataset}` endpoints.
- Multi-stage, non-root Dockerfile with a `/health` HEALTHCHECK.
- Terraform for an AWS data platform: S3 data lake, Glue catalog, pipeline IAM
  role, a reusable network module, and per-environment configuration.
- Apache Airflow DAGs for ETL and scheduled data-quality checks.
- Documentation (README with architecture diagram, `docs/architecture.md`),
  CI workflow with lint/test/terraform/docker jobs, pre-commit hooks,
  issue/PR templates, CODEOWNERS, and Dependabot.
- Open-source project files: LICENSE (MIT), CONTRIBUTING, SECURITY, and
  CODE_OF_CONDUCT.
