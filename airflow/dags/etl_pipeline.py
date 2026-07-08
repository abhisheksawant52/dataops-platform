"""Example ETL DAG: extract -> transform -> load.

This DAG demonstrates how the ``dataops`` package is used inside Airflow tasks:
the transform step registers lineage and the load step is gated on a
data-quality report. It uses the TaskFlow API so intermediate results flow
through XComs.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
from airflow.decorators import dag, task

from dataops.models import Dataset, QualityRule, RuleType
from dataops.service import DataOpsService

DEFAULT_ARGS = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="etl_pipeline",
    description="Extract, transform, and load the daily events dataset.",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["dataops", "etl"],
)
def etl_pipeline():
    """Daily ETL pipeline for the events dataset."""

    @task()
    def extract() -> list[dict]:
        """Extract raw events from the source system."""
        # Placeholder source read; a real task would query a database or API.
        return [
            {"id": 1, "user": "alice", "amount": 12.5},
            {"id": 2, "user": "bob", "amount": 7.0},
        ]

    @task()
    def transform(records: list[dict]) -> list[dict]:
        """Clean and enrich the extracted records, recording lineage."""
        df = pd.DataFrame(records)
        df["amount"] = df["amount"].round(2)

        service = DataOpsService()
        service.register_dataset(Dataset(name="raw_events", columns=list(df.columns)))
        service.register_dataset(Dataset(name="clean_events", columns=list(df.columns)))
        service.link("raw_events", "clean_events", transformation="round_amounts")

        return df.to_dict(orient="records")

    @task()
    def load(records: list[dict]) -> int:
        """Validate quality, then load the cleaned records into the warehouse."""
        df = pd.DataFrame(records)
        service = DataOpsService()
        rules = [
            QualityRule(name="id_not_null", rule_type=RuleType.NOT_NULL, column="id"),
            QualityRule(name="id_unique", rule_type=RuleType.UNIQUE, column="id"),
        ]
        report = service.validate(df, rules, dataset="clean_events")
        if not report.passed:
            raise ValueError(f"quality gate failed: {report.failed_rules}")
        # Placeholder warehouse write.
        return len(df)

    load(transform(extract()))


etl_pipeline()
