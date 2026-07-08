"""Minimal DAG-based pipeline orchestration.

This module provides a small, dependency-light scheduler: tasks are declared
with their upstream dependencies, ordered topologically with :mod:`networkx`,
and executed sequentially. Each execution produces a
:class:`~dataops.models.TaskRun` so callers can inspect status and timing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

import networkx as nx

from .logging_config import get_logger
from .models import Pipeline, TaskRun, TaskStatus

logger = get_logger(__name__)


@dataclass
class Task:
    """A unit of work in a pipeline.

    Parameters
    ----------
    name:
        Unique task identifier within a pipeline.
    run:
        Optional callable executed when the task runs. If ``None`` the task is
        treated as a no-op checkpoint.
    depends_on:
        Names of tasks that must complete before this task runs.
    """

    name: str
    run: Callable[[], None] | None = None
    depends_on: list[str] = field(default_factory=list)


class CycleError(ValueError):
    """Raised when the declared task graph contains a cycle."""


class DAGRunner:
    """Builds a task DAG, resolves execution order, and runs tasks."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._tasks: dict[str, Task] = {}
        self._graph: nx.DiGraph = nx.DiGraph()

    def add_task(self, task: Task) -> None:
        """Register a task and its dependency edges."""
        self._tasks[task.name] = task
        self._graph.add_node(task.name)
        for upstream in task.depends_on:
            self._graph.add_edge(upstream, task.name)

    def topological_order(self) -> list[str]:
        """Return task names in a valid execution order.

        Raises :class:`CycleError` if the dependency graph is not acyclic.
        """
        if not nx.is_directed_acyclic_graph(self._graph):
            raise CycleError(f"pipeline '{self.name}' contains a dependency cycle")
        return list(nx.topological_sort(self._graph))

    def run(self) -> list[TaskRun]:
        """Execute tasks in topological order, returning their run records."""
        runs: list[TaskRun] = []
        for name in self.topological_order():
            task = self._tasks.get(name, Task(name=name))
            run = TaskRun(task=name, status=TaskStatus.RUNNING, started_at=datetime.utcnow())
            logger.info("task_started", pipeline=self.name, task=name)
            try:
                if task.run is not None:
                    task.run()
                run.status = TaskStatus.SUCCESS
            except Exception as exc:  # noqa: BLE001 - record failure, keep report
                run.status = TaskStatus.FAILED
                run.message = str(exc)
                logger.error("task_failed", pipeline=self.name, task=name, error=str(exc))
            finally:
                run.finished_at = datetime.utcnow()
            runs.append(run)
            if run.status == TaskStatus.FAILED:
                break
        return runs


def runner_from_pipeline(
    pipeline: Pipeline, callables: dict[str, Callable[[], None]] | None = None
) -> DAGRunner:
    """Build a :class:`DAGRunner` from a :class:`~dataops.models.Pipeline` model.

    ``callables`` optionally maps task names to the functions that implement
    them; unmapped tasks become no-op checkpoints.
    """
    callables = callables or {}
    runner = DAGRunner(pipeline.name)
    for task_name, deps in pipeline.tasks.items():
        runner.add_task(
            Task(name=task_name, run=callables.get(task_name), depends_on=list(deps))
        )
    return runner
