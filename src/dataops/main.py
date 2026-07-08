"""FastAPI application exposing the DataOps platform.

Endpoints
---------
- ``GET  /health``            liveness probe
- ``GET  /ready``             readiness probe
- ``GET  /metrics``           minimal process/counter metrics
- ``POST /pipelines/run``     run a declared pipeline DAG
- ``POST /quality/validate``  evaluate quality rules over inline records
- ``GET  /lineage/{dataset}`` upstream/downstream lineage for a dataset
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .config import get_settings
from .logging_config import configure_logging, get_logger
from .models import LineageEdge, Pipeline, QualityRule, TaskRun
from .service import DataOpsService

logger = get_logger(__name__)

_METRICS = {"pipelines_run": 0, "quality_checks": 0, "quality_failures": 0}


class PipelineRunRequest(BaseModel):
    """Request body for running a pipeline."""

    pipeline: Pipeline


class QualityValidateRequest(BaseModel):
    """Request body for validating inline records against rules."""

    dataset: str = "dataset"
    records: list[dict[str, Any]] = Field(default_factory=list)
    rules: list[QualityRule] = Field(default_factory=list)


class LineageSeedRequest(BaseModel):
    """Request body for seeding lineage edges."""

    edges: list[LineageEdge] = Field(default_factory=list)


def create_app() -> FastAPI:
    """Application factory wiring the service and routes together."""
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title="DataOps Platform",
        version=__version__,
        summary="Pipeline orchestration, data quality, and data lineage.",
    )
    service = DataOpsService(settings)
    app.state.service = service

    @app.get("/health", tags=["ops"])
    def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok", "version": __version__}

    @app.get("/ready", tags=["ops"])
    def ready() -> dict[str, str]:
        """Readiness probe reporting the active environment."""
        return {"status": "ready", "environment": settings.env}

    @app.get("/metrics", tags=["ops"])
    def metrics() -> dict[str, int]:
        """Return in-process counters."""
        return dict(_METRICS)

    @app.post("/pipelines/run", tags=["orchestration"])
    def run_pipeline(request: PipelineRunRequest) -> list[TaskRun]:
        """Execute a pipeline DAG and return per-task run records."""
        try:
            runs = service.run_pipeline(request.pipeline)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        _METRICS["pipelines_run"] += 1
        return runs

    @app.post("/quality/validate", tags=["quality"])
    def validate(request: QualityValidateRequest) -> dict[str, Any]:
        """Validate inline records against a set of quality rules."""
        df = pd.DataFrame(request.records)
        report = service.validate(df, request.rules, dataset=request.dataset)
        _METRICS["quality_checks"] += 1
        if not report.passed:
            _METRICS["quality_failures"] += 1
        return report.model_dump()

    @app.post("/lineage", tags=["lineage"])
    def seed_lineage(request: LineageSeedRequest) -> dict[str, int]:
        """Register lineage edges in the graph."""
        for edge in request.edges:
            service.link(edge.source, edge.target, edge.transformation)
        return {"edges": len(request.edges)}

    @app.get("/lineage/{dataset}", tags=["lineage"])
    def lineage(dataset: str) -> dict[str, Any]:
        """Return upstream and downstream lineage for *dataset*."""
        try:
            return service.lineage_for(dataset)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"unknown dataset '{dataset}'") from exc

    return app


app = create_app()


def run() -> None:  # pragma: no cover - thin runtime wrapper
    """Console-script entrypoint: serve the API with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "dataops.main:app",
        host="0.0.0.0",  # noqa: S104 - containerised service binds all interfaces
        port=8000,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":  # pragma: no cover
    run()
