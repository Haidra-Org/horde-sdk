"""A minimal typed directed-acyclic-graph implementation for chain flows.

Deliberately hand-rolled rather than depending on a graph library: chains are small (a handful of nodes), the
operations needed are few, and preserving the node key type through generics keeps the call sites fully typed.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterator


class ChainGraphCycleError(ValueError):
    """Raised when an operation requires an acyclic graph but the graph contains a cycle."""


class TypedChainGraph[NodeKeyT: Hashable]:
    """A small directed graph keyed by hashable node keys, with DAG utilities."""

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._successors: dict[NodeKeyT, list[NodeKeyT]] = {}
        self._predecessors: dict[NodeKeyT, list[NodeKeyT]] = {}

    def __contains__(self, key: NodeKeyT) -> bool:
        """Return whether the node key is in the graph."""
        return key in self._successors

    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self._successors)

    def __iter__(self) -> Iterator[NodeKeyT]:
        """Iterate over the node keys in insertion order."""
        return iter(self._successors)

    def add_node(self, key: NodeKeyT) -> None:
        """Add a node to the graph.

        Args:
            key (NodeKeyT): The node key to add.

        Raises:
            ValueError: If the node already exists.
        """
        if key in self._successors:
            raise ValueError(f"Node {key} already exists in the graph")
        self._successors[key] = []
        self._predecessors[key] = []

    def add_edge(self, source: NodeKeyT, target: NodeKeyT) -> None:
        """Add a directed edge between two existing nodes.

        Args:
            source (NodeKeyT): The edge origin.
            target (NodeKeyT): The edge destination.

        Raises:
            ValueError: If either node is missing, the edge is a self-loop, or the edge already exists.
        """
        if source not in self._successors:
            raise ValueError(f"Source node {source} is not in the graph")
        if target not in self._successors:
            raise ValueError(f"Target node {target} is not in the graph")
        if source == target:
            raise ValueError(f"Self-loop on {source} is not allowed")
        if target in self._successors[source]:
            raise ValueError(f"Edge {source} -> {target} already exists")

        self._successors[source].append(target)
        self._predecessors[target].append(source)

    def successors(self, key: NodeKeyT) -> tuple[NodeKeyT, ...]:
        """Return the direct successors of a node."""
        return tuple(self._successors[key])

    def predecessors(self, key: NodeKeyT) -> tuple[NodeKeyT, ...]:
        """Return the direct predecessors of a node."""
        return tuple(self._predecessors[key])

    def sources(self) -> tuple[NodeKeyT, ...]:
        """Return the nodes with no predecessors."""
        return tuple(key for key, preds in self._predecessors.items() if not preds)

    def sinks(self) -> tuple[NodeKeyT, ...]:
        """Return the nodes with no successors."""
        return tuple(key for key, succs in self._successors.items() if not succs)

    def descendants(self, key: NodeKeyT) -> set[NodeKeyT]:
        """Return all nodes reachable from a node, excluding the node itself."""
        seen: set[NodeKeyT] = set()
        frontier = deque(self._successors[key])
        while frontier:
            current = frontier.popleft()
            if current in seen:
                continue
            seen.add(current)
            frontier.extend(self._successors[current])
        return seen

    def is_connected(self) -> bool:
        """Return whether the graph is weakly connected (or empty)."""
        if not self._successors:
            return True

        start = next(iter(self._successors))
        seen: set[NodeKeyT] = {start}
        frontier = deque([start])
        while frontier:
            current = frontier.popleft()
            for neighbor in (*self._successors[current], *self._predecessors[current]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    frontier.append(neighbor)
        return len(seen) == len(self._successors)

    def topological_order(self) -> tuple[NodeKeyT, ...]:
        """Return the nodes in a topological order (Kahn's algorithm).

        Returns:
            tuple[NodeKeyT, ...]: The nodes such that every edge points from an earlier node to a later one.

        Raises:
            ChainGraphCycleError: If the graph contains a cycle.
        """
        in_degree = {key: len(preds) for key, preds in self._predecessors.items()}
        frontier = deque(key for key, degree in in_degree.items() if degree == 0)
        order: list[NodeKeyT] = []

        while frontier:
            current = frontier.popleft()
            order.append(current)
            for successor in self._successors[current]:
                in_degree[successor] -= 1
                if in_degree[successor] == 0:
                    frontier.append(successor)

        if len(order) != len(self._successors):
            unresolved = sorted(str(key) for key, degree in in_degree.items() if degree > 0)
            raise ChainGraphCycleError(f"Graph contains a cycle involving: {', '.join(unresolved)}")

        return tuple(order)

    def is_directed_acyclic(self) -> bool:
        """Return whether the graph is a DAG."""
        try:
            self.topological_order()
        except ChainGraphCycleError:
            return False
        return True
