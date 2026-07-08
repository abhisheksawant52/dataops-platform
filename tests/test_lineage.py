"""Tests for the lineage graph."""

import pytest

from dataops.lineage import LineageGraph
from dataops.models import Dataset


def _sample_graph() -> LineageGraph:
    graph = LineageGraph()
    graph.register_dataset(Dataset(name="raw_events"))
    graph.register_transformation("raw_events", "clean_events", "dedupe")
    graph.register_transformation("clean_events", "daily_metrics", "aggregate")
    return graph


def test_upstream_and_downstream_are_transitive():
    graph = _sample_graph()

    assert graph.upstream("daily_metrics") == ["clean_events", "raw_events"]
    assert graph.downstream("raw_events") == ["clean_events", "daily_metrics"]


def test_cycle_is_rejected():
    graph = _sample_graph()

    with pytest.raises(ValueError):
        graph.register_transformation("daily_metrics", "raw_events")


def test_serialisation_round_trips_nodes_and_edges():
    graph = _sample_graph()

    data = graph.to_dict()

    assert {n["name"] for n in data["nodes"]} >= {"raw_events", "clean_events", "daily_metrics"}
    assert {"source": "raw_events", "target": "clean_events", "transformation": "dedupe"} in data[
        "edges"
    ]
