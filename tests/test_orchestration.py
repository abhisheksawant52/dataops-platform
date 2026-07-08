"""Tests for the DAG orchestration engine."""

import pytest

from dataops.models import Pipeline, TaskStatus
from dataops.orchestration import CycleError, DAGRunner, Task, runner_from_pipeline


def test_topological_order_respects_dependencies():
    runner = DAGRunner("etl")
    runner.add_task(Task(name="extract"))
    runner.add_task(Task(name="transform", depends_on=["extract"]))
    runner.add_task(Task(name="load", depends_on=["transform"]))

    order = runner.topological_order()

    assert order.index("extract") < order.index("transform") < order.index("load")


def test_cycle_is_detected():
    runner = DAGRunner("bad")
    runner.add_task(Task(name="a", depends_on=["b"]))
    runner.add_task(Task(name="b", depends_on=["a"]))

    with pytest.raises(CycleError):
        runner.topological_order()


def test_run_executes_in_order_and_tracks_status():
    calls: list[str] = []
    pipeline = Pipeline(
        name="etl",
        tasks={"extract": [], "transform": ["extract"], "load": ["transform"]},
    )
    callables = {name: (lambda n=name: calls.append(n)) for name in pipeline.tasks}

    runner = runner_from_pipeline(pipeline, callables)
    runs = runner.run()

    assert calls == ["extract", "transform", "load"]
    assert all(r.status == TaskStatus.SUCCESS for r in runs)
