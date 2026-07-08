"""Data-quality DAG: run expectations against curated datasets.

Schedules a standalone quality sweep independent of the ETL run so that data
freshness and integrity are monitored continuously. Failures raise, which
surfaces as a failed Airflow task and can trigger alerting.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
from airflow.decorators import dag, task

from dataops.models import QualityRule, RuleType
from dataops.service import DataOpsService

DATASETS = ["clean_events", "daily_metrics"]


@dag(
    dag_id="data_quality_checks",
    description="Run data-quality expectations across curated datasets.",
    schedule="@hourly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["dataops", "quality"],
)
def data_quality_checks():
    """Hourly data-quality validation sweep."""

    @task()
    def load_dataset(name: str) -> dict:
        """Load a dataset snapshot for validation (placeholder source)."""
        df = pd.DataFrame({"id": [1, 2, 3], "amount": [10.0, 20.0, 30.0]})
        return {"name": name, "records": df.to_dict(orient="records")}

    @task()
    def validate(payload: dict) -> bool:
        """Validate the dataset against its quality rules."""
        df = pd.DataFrame(payload["records"])
        service = DataOpsService()
        rules = [
            QualityRule(name="id_not_null", rule_type=RuleType.NOT_NULL, column="id"),
            QualityRule(
                name="amount_range",
                rule_type=RuleType.IN_RANGE,
                column="amount",
                params={"min": 0, "max": 1_000_000},
            ),
            QualityRule(
                name="row_count",
                rule_type=RuleType.ROW_COUNT_BETWEEN,
                params={"min": 1},
            ),
        ]
        report = service.validate(df, rules, dataset=payload["name"])
        if not report.passed:
            raise ValueError(f"{payload['name']} failed quality: {report.failed_rules}")
        return True

    for dataset in DATASETS:
        validate(load_dataset(dataset))


data_quality_checks()
