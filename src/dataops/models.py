"""Pydantic models shared across the DataOps platform.

These models define the wire and storage contracts for datasets, pipelines,
task runs, data-quality rules and reports, and lineage edges. They are used by
the FastAPI layer for request/response validation and by the core engines for
in-memory bookkeeping.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Supported data-quality expectation types."""

    NOT_NULL = "not_null"
    UNIQUE = "unique"
    IN_RANGE = "in_range"
    REGEX_MATCH = "regex_match"
    ROW_COUNT_BETWEEN = "row_count_between"


class TaskStatus(str, Enum):
    """Lifecycle states for an orchestrated task."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class Dataset(BaseModel):
    """A logical dataset tracked for lineage and quality."""

    name: str
    description: str = ""
    columns: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class QualityRule(BaseModel):
    """A single data-quality expectation applied to a dataset."""

    name: str
    rule_type: RuleType
    column: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class RuleResult(BaseModel):
    """The outcome of evaluating one :class:`QualityRule`."""

    rule: str
    rule_type: RuleType
    column: str | None = None
    passed: bool
    observed: dict[str, Any] = Field(default_factory=dict)
    message: str = ""


class QualityReport(BaseModel):
    """Aggregated result of evaluating rules over a dataset."""

    dataset: str
    results: list[RuleResult] = Field(default_factory=list)
    passed: bool = True
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def failed_rules(self) -> list[RuleResult]:
        """Return the subset of results that did not pass."""
        return [r for r in self.results if not r.passed]


class TaskRun(BaseModel):
    """A single execution record for a task within a pipeline run."""

    task: str
    status: TaskStatus = TaskStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str = ""


class Pipeline(BaseModel):
    """A directed acyclic graph of tasks keyed by dependency edges.

    ``tasks`` maps a task name to the list of task names it depends on.
    """

    name: str
    description: str = ""
    tasks: dict[str, list[str]] = Field(default_factory=dict)


class LineageEdge(BaseModel):
    """A directed lineage relationship between two datasets."""

    source: str
    target: str
    transformation: str = ""
