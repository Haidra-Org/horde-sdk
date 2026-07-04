"""Chain flow construction and validation.

A `ChainFlow` is the immutable routing plan for a unit of work: which stages exist, what they require, and how
they connect. Build one with `ChainFlowBuilder`; the build step validates the topology once so consumers can rely
on the flow's shape without re-checking.
"""

from __future__ import annotations

from horde_sdk.worker.chaining.consts import CHAIN_EDGE_KIND
from horde_sdk.worker.chaining.edges import ChainEdge
from horde_sdk.worker.chaining.graph import TypedChainGraph
from horde_sdk.worker.chaining.nodes import ChainNodeHandle, ChainStageNode
from horde_sdk.worker.consts import GENERATION_PROGRESS


class ChainFlowValidationError(ValueError):
    """Raised when a chain flow fails structural validation at build time."""


class ChainFlow:
    """An immutable, validated directed acyclic graph of stage nodes.

    Instances are created by `ChainFlowBuilder.build`; the constructor assumes already-validated inputs.
    """

    def __init__(
        self,
        *,
        graph: TypedChainGraph[ChainNodeHandle],
        nodes: dict[ChainNodeHandle, ChainStageNode],
        edges: dict[tuple[ChainNodeHandle, ChainNodeHandle], ChainEdge],
    ) -> None:
        """Initialize the flow from builder-validated parts.

        Args:
            graph (TypedChainGraph[ChainNodeHandle]): The validated topology.
            nodes (dict[ChainNodeHandle, ChainStageNode]): The node payloads keyed by handle.
            edges (dict[tuple[ChainNodeHandle, ChainNodeHandle], ChainEdge]): The edge payloads keyed by
                (source, target).
        """
        self._graph = graph
        self._nodes = dict(nodes)
        self._edges = dict(edges)
        self._topological_order = graph.topological_order()
        self._entry_progress_index = {node.entry_progress: node.handle for node in nodes.values()}
        self._completion_progress_index = {node.completion_progress: node.handle for node in nodes.values()}

    @property
    def handles(self) -> tuple[ChainNodeHandle, ...]:
        """The node handles in topological order."""
        return self._topological_order

    @property
    def nodes(self) -> tuple[ChainStageNode, ...]:
        """The stage nodes in topological order."""
        return tuple(self._nodes[handle] for handle in self._topological_order)

    @property
    def edges(self) -> tuple[ChainEdge, ...]:
        """All edges in the flow."""
        return tuple(self._edges.values())

    @property
    def source_handle(self) -> ChainNodeHandle:
        """The handle of the flow's single starting node."""
        return self._graph.sources()[0]

    def get_node(self, handle: ChainNodeHandle) -> ChainStageNode:
        """Return the stage node for a handle.

        Args:
            handle (ChainNodeHandle): The handle to resolve.

        Raises:
            KeyError: If the handle is not part of this flow.
        """
        return self._nodes[handle]

    def get_node_handle(self, name: str) -> ChainNodeHandle:
        """Return the handle for a node name.

        Args:
            name (str): The node name.

        Raises:
            KeyError: If no node has the given name.
        """
        handle = ChainNodeHandle(name=name)
        if handle not in self._nodes:
            raise KeyError(f"No node named '{name}' in this flow")
        return handle

    def get_edge(self, source: ChainNodeHandle, target: ChainNodeHandle) -> ChainEdge:
        """Return the edge between two handles.

        Args:
            source (ChainNodeHandle): The edge origin.
            target (ChainNodeHandle): The edge destination.

        Raises:
            KeyError: If there is no such edge.
        """
        return self._edges[(source, target)]

    def successors(self, handle: ChainNodeHandle) -> tuple[ChainNodeHandle, ...]:
        """Return the direct successors of a node."""
        return self._graph.successors(handle)

    def predecessors(self, handle: ChainNodeHandle) -> tuple[ChainNodeHandle, ...]:
        """Return the direct predecessors of a node."""
        return self._graph.predecessors(handle)

    def descendants(self, handle: ChainNodeHandle) -> set[ChainNodeHandle]:
        """Return all nodes reachable from a node, excluding the node itself."""
        return self._graph.descendants(handle)

    def node_for_entry_progress(self, progress: GENERATION_PROGRESS) -> ChainNodeHandle | None:
        """Return the node whose stage begins at the given generation progress, if any."""
        return self._entry_progress_index.get(progress)

    def node_for_completion_progress(self, progress: GENERATION_PROGRESS) -> ChainNodeHandle | None:
        """Return the node whose stage completes at the given generation progress, if any."""
        return self._completion_progress_index.get(progress)


class ChainFlowBuilder:
    """Accumulates stage nodes and edges, then validates and freezes them into a `ChainFlow`."""

    def __init__(self) -> None:
        """Initialize an empty builder."""
        self._graph: TypedChainGraph[ChainNodeHandle] = TypedChainGraph()
        self._nodes: dict[ChainNodeHandle, ChainStageNode] = {}
        self._edges: dict[tuple[ChainNodeHandle, ChainNodeHandle], ChainEdge] = {}

    def add_stage(self, node: ChainStageNode) -> ChainNodeHandle:
        """Add a stage node to the flow under construction.

        Args:
            node (ChainStageNode): The stage to add.

        Returns:
            ChainNodeHandle: The handle referring to the added node.

        Raises:
            ChainFlowValidationError: If a node with the same name already exists.
        """
        handle = node.handle
        if handle in self._nodes:
            raise ChainFlowValidationError(f"A node named '{node.name}' already exists in this flow")
        self._graph.add_node(handle)
        self._nodes[handle] = node
        return handle

    def connect(
        self,
        source: ChainNodeHandle,
        target: ChainNodeHandle,
        kind: CHAIN_EDGE_KIND = CHAIN_EDGE_KIND.SAME_GENERATION,
        *,
        edge: ChainEdge | None = None,
    ) -> ChainEdge:
        """Connect two stages with a directed edge.

        Args:
            source (ChainNodeHandle): The stage whose completion feeds the edge.
            target (ChainNodeHandle): The stage that becomes eligible when the edge fires.
            kind (CHAIN_EDGE_KIND, optional): The edge kind for a default edge.
                Defaults to CHAIN_EDGE_KIND.SAME_GENERATION.
            edge (ChainEdge | None, optional): A pre-built edge to use instead of constructing a default one.
                Its source and target must match the given handles. Defaults to None.

        Returns:
            ChainEdge: The edge that was added.

        Raises:
            ChainFlowValidationError: If either handle is unknown or the edge endpoints do not match.
        """
        if source not in self._nodes:
            raise ChainFlowValidationError(f"Unknown source node '{source}'")
        if target not in self._nodes:
            raise ChainFlowValidationError(f"Unknown target node '{target}'")

        if edge is None:
            edge = ChainEdge(kind=kind, source=source, target=target)
        elif edge.source != source or edge.target != target:
            raise ChainFlowValidationError(
                f"Edge endpoints ({edge.source} -> {edge.target}) do not match connect() arguments "
                f"({source} -> {target})",
            )

        self._graph.add_edge(source, target)
        self._edges[(source, target)] = edge
        return edge

    def build(self) -> ChainFlow:
        """Validate the accumulated topology and freeze it into a `ChainFlow`.

        Returns:
            ChainFlow: The validated flow.

        Raises:
            ChainFlowValidationError: If the flow is empty, cyclic, disconnected, has multiple starting nodes,
                or two stages share an entry or completion progress state.
        """
        if not self._nodes:
            raise ChainFlowValidationError("A chain flow requires at least one stage")

        if not self._graph.is_directed_acyclic():
            raise ChainFlowValidationError("A chain flow must be acyclic")

        if not self._graph.is_connected():
            raise ChainFlowValidationError("A chain flow must be connected; found unreachable stages")

        flow_sources = self._graph.sources()
        if len(flow_sources) != 1:
            source_names = ", ".join(str(handle) for handle in flow_sources)
            raise ChainFlowValidationError(f"A chain flow requires exactly one starting stage; found: {source_names}")

        entry_progress_seen: dict[GENERATION_PROGRESS, ChainNodeHandle] = {}
        completion_progress_seen: dict[GENERATION_PROGRESS, ChainNodeHandle] = {}
        for handle, node in self._nodes.items():
            if node.entry_progress in entry_progress_seen:
                raise ChainFlowValidationError(
                    f"Stages '{entry_progress_seen[node.entry_progress]}' and '{handle}' share entry progress "
                    f"{node.entry_progress}; progress-driven routing requires unique stage boundaries",
                )
            if node.completion_progress in completion_progress_seen:
                raise ChainFlowValidationError(
                    f"Stages '{completion_progress_seen[node.completion_progress]}' and '{handle}' share "
                    f"completion progress {node.completion_progress}; progress-driven routing requires unique "
                    "stage boundaries",
                )
            entry_progress_seen[node.entry_progress] = handle
            completion_progress_seen[node.completion_progress] = handle

        return ChainFlow(graph=self._graph, nodes=self._nodes, edges=self._edges)
