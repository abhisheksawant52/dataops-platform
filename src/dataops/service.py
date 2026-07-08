"""High-level orchestrator tying together the platform's engines.

:class:`DataOpsService` is the single entry point used by the API layer and by
Airflow tasks. It owns a shared :class:`~dataops.lineage.LineageGraph` and knows
how to run pipelines and validate dataframes against quality rules.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

import pandas as pd

from . import quality
from .config import Settings, get_settings
from .lineage import LineageGraph
from .logging_config import get_logger
from .models import Dataset, Pipeline, QualityReport, QualityRule, TaskRun
from .orchestration import runner_from_pipeline

logger = get_logger(__name__)


class DataOpsService:
    """Coordinates orchestration, data quality, and lineage."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.lineage = LineageGraph()

    # -- Orchestration ---------------------------------------------------
    def run_pipeline(
        self,
        pipeline: Pipeline,
        callables: dict[str, Callable[[], None]] | None = None,
    ) -> list[TaskRun]:
        """Execute *pipeline* and return the resulting task-run records."""
        logger.info("pipeline_run", pipeline=pipeline.name, tasks=len(pipeline.tasks))
        runner = runner_from_pipeline(pipeline, callables)
        return runner.run()

    # -- Data quality ----------------------------------------------------
    def validate(
        self,
        df: pd.DataFrame,
        rules: Iterable[QualityRule],
        dataset: str = "dataset",
    ) -> QualityReport:
        """Validate *df* against *rules* using the configured fail threshold."""
        report = quality.evaluate(
            df,
            rules,
            dataset=dataset,
            fail_threshold=self.settings.quality_fail_threshold,
        )
        logger.info(
            "quality_report",
            dataset=dataset,
            passed=report.passed,
            failures=len(report.failed_rules),
        )
        return report

    # -- Lineage ---------------------------------------------------------
    def register_dataset(self, dataset: Dataset) -> None:
        """Register a dataset node in the lineage graph."""
        self.lineage.register_dataset(dataset)

    def link(self, source: str, target: str, transformation: str = "") -> None:
        """Record a lineage edge ``source -> target``."""
        self.lineage.register_transformation(source, target, transformation)

    def lineage_for(self, dataset: str) -> dict:
        """Return upstream and downstream datasets for *dataset*."""
        return {
            "dataset": dataset,
            "upstream": self.lineage.upstream(dataset),
            "downstream": self.lineage.downstream(dataset),
        }
