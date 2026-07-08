"""Data-lineage graph backed by :mod:`networkx`.

The :class:`LineageGraph` records datasets as nodes and transformations as
directed edges (source -> target). It supports upstream/downstream traversal
and serialisation to a plain dict / JSON for storage or API responses.
"""

from __future__ import annotations

import json

import networkx as nx

from .models import Dataset, LineageEdge


class LineageGraph:
    """A directed acyclic graph of datasets and the transformations between them."""

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()

    def register_dataset(self, dataset: Dataset) -> None:
        """Add or update a dataset node."""
        self._graph.add_node(
            dataset.name,
            description=dataset.description,
            columns=list(dataset.columns),
            tags=list(dataset.tags),
        )

    def register_transformation(
        self, source: str, target: str, transformation: str = ""
    ) -> LineageEdge:
        """Record a directed edge ``source -> target``.

        Nodes are created on demand if they were not registered explicitly.
        Raises :class:`ValueError` if the edge would introduce a cycle.
        """
        self._graph.add_node(source)
        self._graph.add_node(target)
        self._graph.add_edge(source, target, transformation=transformation)
        if not nx.is_directed_acyclic_graph(self._graph):
            self._graph.remove_edge(source, target)
            raise ValueError(f"edge {source} -> {target} would introduce a cycle")
        return LineageEdge(source=source, target=target, transformation=transformation)

    def upstream(self, dataset: str) -> list[str]:
        """Return all datasets that *dataset* transitively depends on."""
        if dataset not in self._graph:
            raise KeyError(dataset)
        return sorted(nx.ancestors(self._graph, dataset))

    def downstream(self, dataset: str) -> list[str]:
        """Return all datasets transitively derived from *dataset*."""
        if dataset not in self._graph:
            raise KeyError(dataset)
        return sorted(nx.descendants(self._graph, dataset))

    def to_dict(self) -> dict:
        """Serialise the graph to a JSON-friendly dict."""
        return {
            "nodes": [
                {"name": name, **{k: v for k, v in data.items()}}
                for name, data in self._graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    "transformation": data.get("transformation", ""),
                }
                for source, target, data in self._graph.edges(data=True)
            ],
        }

    def to_json(self, indent: int | None = 2) -> str:
        """Serialise the graph to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
