"""Composable, chainable descriptions of worker units of work.

A unit of work is described as a small directed acyclic graph of stages (`ChainFlow`), where each stage names the
kind of work, the lane capability it requires, and the generation-progress states that bound it. One
`HordeSingleGeneration` flows through the stages of its chain; `ChainExecutionContext.advance_for_progress` keeps
the chain state in lockstep with the generation's state machine.

Deliberately out of scope in this iteration: flow serialization, merge/fan-in barriers, retry policies (workers
own their fault logic), and whole-job chain nodes that build new units of work from finished ones.
"""

from horde_sdk.worker.chaining.common_flows import (
    GENERATE_STAGE_NAME,
    POST_PROCESS_STAGE_NAME,
    SAFETY_CHECK_STAGE_NAME,
    SUBMIT_STAGE_NAME,
    alchemy_flow,
    image_generation_flow,
    text_generation_flow,
)
from horde_sdk.worker.chaining.consts import (
    CHAIN_CAPABILITY,
    CHAIN_EDGE_KIND,
    CHAIN_NODE_KIND,
    CHAIN_NODE_STATE,
)
from horde_sdk.worker.chaining.context import ChainConsistencyError, ChainExecutionContext
from horde_sdk.worker.chaining.edges import ChainEdge
from horde_sdk.worker.chaining.executors import ChainExecutor, LocalChainExecutor, StageWorkCallable
from horde_sdk.worker.chaining.flow import ChainFlow, ChainFlowBuilder, ChainFlowValidationError
from horde_sdk.worker.chaining.graph import ChainGraphCycleError, TypedChainGraph
from horde_sdk.worker.chaining.nodes import ChainNodeHandle, ChainStageNode

__all__ = [
    "CHAIN_CAPABILITY",
    "CHAIN_EDGE_KIND",
    "CHAIN_NODE_KIND",
    "CHAIN_NODE_STATE",
    "GENERATE_STAGE_NAME",
    "POST_PROCESS_STAGE_NAME",
    "SAFETY_CHECK_STAGE_NAME",
    "SUBMIT_STAGE_NAME",
    "ChainConsistencyError",
    "ChainEdge",
    "ChainExecutionContext",
    "ChainExecutor",
    "ChainFlow",
    "ChainFlowBuilder",
    "ChainFlowValidationError",
    "ChainGraphCycleError",
    "ChainNodeHandle",
    "ChainStageNode",
    "LocalChainExecutor",
    "StageWorkCallable",
    "TypedChainGraph",
    "alchemy_flow",
    "image_generation_flow",
    "text_generation_flow",
]
