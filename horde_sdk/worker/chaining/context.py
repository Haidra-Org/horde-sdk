"""Per-unit-of-work chain execution state.

A `ChainExecutionContext` tracks each stage node's execution state for one unit of work. It is descriptive: the
owning orchestration performs the actual work and reports progress here, either by marking nodes directly or by
feeding generation-progress values through `advance_for_progress`.
"""

from __future__ import annotations

import threading
import time

from horde_sdk.worker.chaining.consts import CHAIN_NODE_STATE
from horde_sdk.worker.chaining.flow import ChainFlow
from horde_sdk.worker.chaining.nodes import ChainNodeHandle
from horde_sdk.worker.consts import GENERATION_PROGRESS

_TERMINAL_NODE_STATES = {
    CHAIN_NODE_STATE.COMPLETED,
    CHAIN_NODE_STATE.FAILED,
    CHAIN_NODE_STATE.SKIPPED,
}

_TERMINAL_FAILURE_PROGRESS = {
    GENERATION_PROGRESS.ABORTED,
    GENERATION_PROGRESS.REPORTED_FAILED,
    GENERATION_PROGRESS.ABANDONED,
    GENERATION_PROGRESS.USER_REQUESTED_ABORT,
    GENERATION_PROGRESS.USER_ABORT_COMPLETE,
}


class ChainConsistencyError(RuntimeError):
    """Raised when a reported progression contradicts the chain's routing plan."""


class ChainExecutionContext:
    """Thread-safe execution state for one traversal of a `ChainFlow`."""

    def __init__(self, flow: ChainFlow) -> None:
        """Initialize all nodes as pending.

        Args:
            flow (ChainFlow): The flow being traversed.
        """
        self._flow = flow
        self._lock = threading.RLock()
        self._states: dict[ChainNodeHandle, CHAIN_NODE_STATE] = dict.fromkeys(
            flow.handles,
            CHAIN_NODE_STATE.PENDING,
        )
        self._errors: dict[ChainNodeHandle, list[str]] = {handle: [] for handle in flow.handles}
        self._started_at: dict[ChainNodeHandle, float] = {}
        self._finished_at: dict[ChainNodeHandle, float] = {}

    @property
    def flow(self) -> ChainFlow:
        """The flow this context tracks."""
        return self._flow

    def node_state(self, handle: ChainNodeHandle) -> CHAIN_NODE_STATE:
        """Return the current state of a node."""
        with self._lock:
            return self._states[handle]

    def node_errors(self, handle: ChainNodeHandle) -> tuple[str, ...]:
        """Return the errors recorded against a node."""
        with self._lock:
            return tuple(self._errors[handle])

    def node_duration(self, handle: ChainNodeHandle) -> float | None:
        """Seconds a node spent executing, or None when it has not both started and finished."""
        with self._lock:
            started = self._started_at.get(handle)
            finished = self._finished_at.get(handle)
            if started is None or finished is None:
                return None
            return finished - started

    def snapshot(self) -> dict[str, CHAIN_NODE_STATE]:
        """Return a point-in-time view of every node's state, keyed by node name."""
        with self._lock:
            return {handle.name: state for handle, state in self._states.items()}

    def _is_dependency_satisfied(self, handle: ChainNodeHandle) -> bool:
        """Whether all predecessors of a node have finished without failing."""
        return all(
            self._states[predecessor] in {CHAIN_NODE_STATE.COMPLETED, CHAIN_NODE_STATE.SKIPPED}
            for predecessor in self._flow.predecessors(handle)
        )

    def ready_nodes(self) -> tuple[ChainNodeHandle, ...]:
        """Return the nodes eligible to start: pending or ready, with all dependencies satisfied."""
        with self._lock:
            return tuple(
                handle
                for handle in self._flow.handles
                if self._states[handle] in {CHAIN_NODE_STATE.PENDING, CHAIN_NODE_STATE.READY}
                and self._is_dependency_satisfied(handle)
            )

    @property
    def is_finished(self) -> bool:
        """Whether every node has reached a terminal state."""
        with self._lock:
            return all(state in _TERMINAL_NODE_STATES for state in self._states.values())

    @property
    def has_failed(self) -> bool:
        """Whether any node failed."""
        with self._lock:
            return any(state == CHAIN_NODE_STATE.FAILED for state in self._states.values())

    def mark_executing(self, handle: ChainNodeHandle) -> None:
        """Mark a node as executing.

        Optional pending predecessors are skipped implicitly; a required predecessor that has not finished is a
        routing contradiction.

        Args:
            handle (ChainNodeHandle): The node that started executing.

        Raises:
            ChainConsistencyError: If the node is already terminal or a required dependency has not finished.
        """
        with self._lock:
            current = self._states[handle]
            if current in _TERMINAL_NODE_STATES or current == CHAIN_NODE_STATE.EXECUTING:
                raise ChainConsistencyError(f"Node '{handle}' cannot start executing from state {current}")

            for predecessor in self._flow.predecessors(handle):
                predecessor_state = self._states[predecessor]
                if predecessor_state in {CHAIN_NODE_STATE.COMPLETED, CHAIN_NODE_STATE.SKIPPED}:
                    continue
                if self._flow.get_node(predecessor).optional:
                    self._skip_subtree_rooted_at(predecessor, reason=f"optional stage bypassed by '{handle}'")
                    continue
                raise ChainConsistencyError(
                    f"Node '{handle}' cannot start: required predecessor '{predecessor}' is {predecessor_state}",
                )

            self._states[handle] = CHAIN_NODE_STATE.EXECUTING
            self._started_at[handle] = time.monotonic()

    def _skip_subtree_rooted_at(self, handle: ChainNodeHandle, *, reason: str) -> None:
        """Skip a non-terminal node; used for optional stages that the traversal bypassed."""
        if self._states[handle] in _TERMINAL_NODE_STATES:
            return
        self._states[handle] = CHAIN_NODE_STATE.SKIPPED
        self._errors[handle].append(reason)

    def mark_completed(self, handle: ChainNodeHandle) -> tuple[ChainNodeHandle, ...]:
        """Mark a node as completed and return the nodes that became eligible as a result.

        Args:
            handle (ChainNodeHandle): The node that finished.

        Returns:
            tuple[ChainNodeHandle, ...]: The successors that are now eligible to start.

        Raises:
            ChainConsistencyError: If the node is already terminal.
        """
        with self._lock:
            current = self._states[handle]
            if current in _TERMINAL_NODE_STATES:
                raise ChainConsistencyError(f"Node '{handle}' cannot complete from state {current}")

            self._states[handle] = CHAIN_NODE_STATE.COMPLETED
            self._finished_at[handle] = time.monotonic()
            if handle not in self._started_at:
                self._started_at[handle] = self._finished_at[handle]

            return tuple(
                successor
                for successor in self._flow.successors(handle)
                if self._states[successor] == CHAIN_NODE_STATE.PENDING and self._is_dependency_satisfied(successor)
            )

    def mark_failed(self, handle: ChainNodeHandle, *, error: str | None = None) -> None:
        """Mark a node as failed and skip everything downstream of it.

        Args:
            handle (ChainNodeHandle): The node that failed.
            error (str | None, optional): A description of the failure. Defaults to None.
        """
        with self._lock:
            self._states[handle] = CHAIN_NODE_STATE.FAILED
            self._finished_at[handle] = time.monotonic()
            if error is not None:
                self._errors[handle].append(error)

            for descendant in self._flow.descendants(handle):
                if self._states[descendant] not in _TERMINAL_NODE_STATES:
                    self._states[descendant] = CHAIN_NODE_STATE.SKIPPED
                    self._errors[descendant].append(f"upstream stage '{handle}' failed")

    def mark_skipped(self, handle: ChainNodeHandle, *, reason: str | None = None) -> None:
        """Mark a node as skipped.

        Args:
            handle (ChainNodeHandle): The node to skip.
            reason (str | None, optional): Why the node was skipped. Defaults to None.

        Raises:
            ChainConsistencyError: If the node is not optional or is already terminal.
        """
        with self._lock:
            if not self._flow.get_node(handle).optional:
                raise ChainConsistencyError(f"Node '{handle}' is required and cannot be skipped explicitly")
            if self._states[handle] in _TERMINAL_NODE_STATES:
                raise ChainConsistencyError(f"Node '{handle}' is already {self._states[handle]}")
            self._states[handle] = CHAIN_NODE_STATE.SKIPPED
            if reason is not None:
                self._errors[handle].append(reason)

    def advance_for_progress(self, progress: GENERATION_PROGRESS) -> tuple[ChainNodeHandle, ...]:
        """Advance the chain state from a generation-progress observation.

        This is the bridge that lets an orchestrator drive the chain purely from the generation's state machine:
        a stage's `entry_progress` marks its node executing, a stage's `completion_progress` marks its node
        completed, and a terminal failure progress fails whichever node is executing.

        Args:
            progress (GENERATION_PROGRESS): The progress value the generation just reached.

        Returns:
            tuple[ChainNodeHandle, ...]: The nodes that became eligible to start due to this observation.
        """
        with self._lock:
            if progress in _TERMINAL_FAILURE_PROGRESS:
                for handle in self._flow.handles:
                    if self._states[handle] == CHAIN_NODE_STATE.EXECUTING:
                        self.mark_failed(handle, error=f"generation reached {progress}")
                return ()

            entering = self._flow.node_for_entry_progress(progress)
            if entering is not None and self._states[entering] in {
                CHAIN_NODE_STATE.PENDING,
                CHAIN_NODE_STATE.READY,
            }:
                self.mark_executing(entering)

            completing = self._flow.node_for_completion_progress(progress)
            if completing is not None and self._states[completing] not in _TERMINAL_NODE_STATES:
                newly_ready = self.mark_completed(completing)
                for handle in newly_ready:
                    self._states[handle] = CHAIN_NODE_STATE.READY
                return newly_ready

            return ()
