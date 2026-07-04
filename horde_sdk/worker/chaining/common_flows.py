"""Canonical chain flows for the standard worker workloads.

These builders are the single construction point for the flows a worker routes internally. Stage boundaries are
expressed as generation-progress states, so a `ChainExecutionContext` over one of these flows can be driven
entirely by `advance_for_progress`.
"""

from __future__ import annotations

from itertools import pairwise

from horde_sdk.worker.chaining.consts import CHAIN_CAPABILITY, CHAIN_NODE_KIND
from horde_sdk.worker.chaining.flow import ChainFlow, ChainFlowBuilder
from horde_sdk.worker.chaining.nodes import ChainStageNode
from horde_sdk.worker.consts import GENERATION_PROGRESS

GENERATE_STAGE_NAME = "generate"
POST_PROCESS_STAGE_NAME = "post_process"
SAFETY_CHECK_STAGE_NAME = "safety_check"
SUBMIT_STAGE_NAME = "submit"


def _generate_stage() -> ChainStageNode:
    return ChainStageNode(
        name=GENERATE_STAGE_NAME,
        kind=CHAIN_NODE_KIND.GENERATE,
        entry_progress=GENERATION_PROGRESS.GENERATING,
        completion_progress=GENERATION_PROGRESS.GENERATION_COMPLETE,
        required_capability=CHAIN_CAPABILITY.INFERENCE,
    )


def _post_process_stage() -> ChainStageNode:
    return ChainStageNode(
        name=POST_PROCESS_STAGE_NAME,
        kind=CHAIN_NODE_KIND.POST_PROCESS,
        entry_progress=GENERATION_PROGRESS.POST_PROCESSING,
        completion_progress=GENERATION_PROGRESS.POST_PROCESSING_COMPLETE,
        required_capability=CHAIN_CAPABILITY.POST_PROCESSING,
    )


def _safety_check_stage() -> ChainStageNode:
    return ChainStageNode(
        name=SAFETY_CHECK_STAGE_NAME,
        kind=CHAIN_NODE_KIND.SAFETY_CHECK,
        entry_progress=GENERATION_PROGRESS.SAFETY_CHECKING,
        completion_progress=GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE,
        required_capability=CHAIN_CAPABILITY.SAFETY,
    )


def _submit_stage() -> ChainStageNode:
    return ChainStageNode(
        name=SUBMIT_STAGE_NAME,
        kind=CHAIN_NODE_KIND.SUBMIT,
        entry_progress=GENERATION_PROGRESS.SUBMITTING,
        completion_progress=GENERATION_PROGRESS.SUBMIT_COMPLETE,
        required_capability=None,
    )


def _build_linear_flow(stages: list[ChainStageNode]) -> ChainFlow:
    """Build a flow from stages connected in sequence."""
    builder = ChainFlowBuilder()
    handles = [builder.add_stage(stage) for stage in stages]
    for source, target in pairwise(handles):
        builder.connect(source, target)
    return builder.build()


def image_generation_flow(
    *,
    post_processing: bool,
    safety_check: bool,
    submit: bool = True,
) -> ChainFlow:
    """Build the flow for an image generation unit of work.

    Args:
        post_processing (bool): Whether the work includes a post-processing stage.
        safety_check (bool): Whether the work includes a safety-check stage.
        submit (bool, optional): Whether the work includes a submit stage. Defaults to True.

    Returns:
        ChainFlow: generate -> (post_process) -> (safety_check) -> (submit).
    """
    stages = [_generate_stage()]
    if post_processing:
        stages.append(_post_process_stage())
    if safety_check:
        stages.append(_safety_check_stage())
    if submit:
        stages.append(_submit_stage())
    return _build_linear_flow(stages)


def alchemy_flow(
    *,
    safety_check: bool = False,
    submit: bool = True,
) -> ChainFlow:
    """Build the flow for a standalone alchemy (post-processing) unit of work.

    Args:
        safety_check (bool, optional): Whether the work includes a safety-check stage. Defaults to False.
        submit (bool, optional): Whether the work includes a submit stage. Defaults to True.

    Returns:
        ChainFlow: post_process -> (safety_check) -> (submit).
    """
    stages = [_post_process_stage()]
    if safety_check:
        stages.append(_safety_check_stage())
    if submit:
        stages.append(_submit_stage())
    return _build_linear_flow(stages)


def text_generation_flow(
    *,
    safety_check: bool = False,
    submit: bool = True,
) -> ChainFlow:
    """Build the flow for a text generation unit of work.

    Args:
        safety_check (bool, optional): Whether the work includes a safety-check stage. Defaults to False.
        submit (bool, optional): Whether the work includes a submit stage. Defaults to True.

    Returns:
        ChainFlow: generate -> (safety_check) -> (submit).
    """
    stages = [_generate_stage()]
    if safety_check:
        stages.append(_safety_check_stage())
    if submit:
        stages.append(_submit_stage())
    return _build_linear_flow(stages)
