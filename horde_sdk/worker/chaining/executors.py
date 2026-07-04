"""Chain executors.

Production workers are their own executors: their orchestration loops report progress into a
`ChainExecutionContext` (typically via `advance_for_progress`) and consult `ready_nodes` for routing. The
`LocalChainExecutor` here is the reference implementation for simple consumers and tests: a synchronous
topological walk with a pluggable work callable.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from horde_sdk.worker.chaining.consts import CHAIN_NODE_STATE
from horde_sdk.worker.chaining.context import ChainExecutionContext
from horde_sdk.worker.chaining.flow import ChainFlow
from horde_sdk.worker.chaining.nodes import ChainStageNode
from horde_sdk.worker.consts import GENERATION_PROGRESS

StageWorkCallable = Callable[[ChainStageNode], GENERATION_PROGRESS]
"""Performs a stage's work and returns the generation progress it reached.

Returning the stage's `completion_progress` marks the stage completed; returning a failing progress fails it.
"""


class ChainExecutor(Protocol):
    """Anything that can traverse a chain flow and produce a finished execution context."""

    def execute(
        self,
        flow: ChainFlow,
        work: StageWorkCallable,
    ) -> ChainExecutionContext:
        """Traverse the flow, performing each stage's work.

        Args:
            flow (ChainFlow): The flow to traverse.
            work (StageWorkCallable): The callable that performs a stage's work.

        Returns:
            ChainExecutionContext: The finished execution context.
        """
        ...


class LocalChainExecutor:
    """A synchronous, single-threaded reference executor."""

    def execute(
        self,
        flow: ChainFlow,
        work: StageWorkCallable,
    ) -> ChainExecutionContext:
        """Walk the flow in topological order, performing each stage's work.

        A stage whose work returns a progress other than its completion progress is treated as failed, which
        skips all downstream stages. Stages skipped by an earlier failure are not executed.

        Args:
            flow (ChainFlow): The flow to traverse.
            work (StageWorkCallable): The callable that performs a stage's work.

        Returns:
            ChainExecutionContext: The finished execution context.
        """
        context = ChainExecutionContext(flow)

        for handle in flow.handles:
            if context.node_state(handle) != CHAIN_NODE_STATE.PENDING:
                continue

            node = flow.get_node(handle)
            context.mark_executing(handle)
            reached_progress = work(node)

            if reached_progress == node.completion_progress:
                context.mark_completed(handle)
            else:
                context.mark_failed(
                    handle,
                    error=f"stage work reached {reached_progress}, expected {node.completion_progress}",
                )

        return context
