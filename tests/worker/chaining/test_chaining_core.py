"""Tests for the chaining core: graph, flow building, execution context, executors, and common flows."""

import threading

import pytest

from horde_sdk.generation_parameters.image import ImageGenerationParameters
from horde_sdk.safety import ImageSafetyResult
from horde_sdk.worker.chaining import (
    CHAIN_CAPABILITY,
    CHAIN_NODE_KIND,
    CHAIN_NODE_STATE,
    GENERATE_STAGE_NAME,
    POST_PROCESS_STAGE_NAME,
    SAFETY_CHECK_STAGE_NAME,
    SUBMIT_STAGE_NAME,
    ChainConsistencyError,
    ChainExecutionContext,
    ChainFlowBuilder,
    ChainFlowValidationError,
    ChainGraphCycleError,
    ChainNodeHandle,
    ChainStageNode,
    LocalChainExecutor,
    TypedChainGraph,
    alchemy_flow,
    image_generation_flow,
    text_generation_flow,
)
from horde_sdk.worker.consts import GENERATION_PROGRESS
from horde_sdk.worker.generations import ImageSingleGeneration


class TestTypedChainGraph:
    """The minimal DAG primitive."""

    def test_topological_order_respects_edges(self) -> None:
        """Topological order places every edge source before its target."""
        graph: TypedChainGraph[str] = TypedChainGraph()
        for key in ("a", "b", "c", "d"):
            graph.add_node(key)
        graph.add_edge("a", "b")
        graph.add_edge("a", "c")
        graph.add_edge("b", "d")
        graph.add_edge("c", "d")

        order = graph.topological_order()
        assert order.index("a") < order.index("b") < order.index("d")
        assert order.index("a") < order.index("c") < order.index("d")
        assert graph.is_directed_acyclic()
        assert graph.sources() == ("a",)
        assert graph.sinks() == ("d",)
        assert graph.descendants("a") == {"b", "c", "d"}

    def test_cycle_detection(self) -> None:
        """A cycle is rejected by topological_order and reported by is_directed_acyclic."""
        graph: TypedChainGraph[str] = TypedChainGraph()
        for key in ("a", "b", "c"):
            graph.add_node(key)
        graph.add_edge("a", "b")
        graph.add_edge("b", "c")
        graph.add_edge("c", "a")

        assert not graph.is_directed_acyclic()
        with pytest.raises(ChainGraphCycleError):
            graph.topological_order()

    def test_duplicate_and_dangling_edges_rejected(self) -> None:
        """Self-loops, duplicate edges, and edges to unknown nodes are rejected."""
        graph: TypedChainGraph[str] = TypedChainGraph()
        graph.add_node("a")
        graph.add_node("b")
        graph.add_edge("a", "b")

        with pytest.raises(ValueError, match="already exists"):
            graph.add_edge("a", "b")
        with pytest.raises(ValueError, match="Self-loop"):
            graph.add_edge("a", "a")
        with pytest.raises(ValueError, match="not in the graph"):
            graph.add_edge("a", "zzz")
        with pytest.raises(ValueError, match="already exists"):
            graph.add_node("a")

    def test_connectivity(self) -> None:
        """Weak connectivity distinguishes one component from two."""
        graph: TypedChainGraph[str] = TypedChainGraph()
        for key in ("a", "b", "c"):
            graph.add_node(key)
        graph.add_edge("a", "b")
        assert not graph.is_connected()
        graph.add_edge("b", "c")
        assert graph.is_connected()


def _stage(
    name: str,
    entry: GENERATION_PROGRESS,
    completion: GENERATION_PROGRESS,
    *,
    optional: bool = False,
) -> ChainStageNode:
    return ChainStageNode(
        name=name,
        kind=CHAIN_NODE_KIND.CUSTOM,
        entry_progress=entry,
        completion_progress=completion,
        required_capability=CHAIN_CAPABILITY.CUSTOM,
        optional=optional,
    )


class TestChainFlowBuilder:
    """Structural validation at build time."""

    def test_empty_flow_rejected(self) -> None:
        """A flow with no stages cannot be built."""
        with pytest.raises(ChainFlowValidationError, match="at least one stage"):
            ChainFlowBuilder().build()

    def test_duplicate_stage_name_rejected(self) -> None:
        """Two stages may not share a name."""
        builder = ChainFlowBuilder()
        builder.add_stage(_stage("x", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATION_COMPLETE))
        with pytest.raises(ChainFlowValidationError, match="already exists"):
            builder.add_stage(_stage("x", GENERATION_PROGRESS.POST_PROCESSING, GENERATION_PROGRESS.SUBMITTING))

    def test_multiple_sources_rejected(self) -> None:
        """A flow must have exactly one starting stage."""
        builder = ChainFlowBuilder()
        first = builder.add_stage(
            _stage("first", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATION_COMPLETE),
        )
        second = builder.add_stage(
            _stage("second", GENERATION_PROGRESS.POST_PROCESSING, GENERATION_PROGRESS.POST_PROCESSING_COMPLETE),
        )
        sink = builder.add_stage(
            _stage("sink", GENERATION_PROGRESS.SAFETY_CHECKING, GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE),
        )
        builder.connect(first, sink)
        builder.connect(second, sink)
        with pytest.raises(ChainFlowValidationError, match="exactly one starting stage"):
            builder.build()

    def test_disconnected_flow_rejected(self) -> None:
        """Unreachable stages are rejected."""
        builder = ChainFlowBuilder()
        first = builder.add_stage(
            _stage("first", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATION_COMPLETE),
        )
        second = builder.add_stage(
            _stage("second", GENERATION_PROGRESS.POST_PROCESSING, GENERATION_PROGRESS.POST_PROCESSING_COMPLETE),
        )
        third = builder.add_stage(
            _stage("third", GENERATION_PROGRESS.SAFETY_CHECKING, GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE),
        )
        builder.connect(first, second)
        # third is never connected
        del third
        with pytest.raises(ChainFlowValidationError):
            builder.build()

    def test_shared_progress_boundaries_rejected(self) -> None:
        """Two stages may not claim the same entry or completion progress."""
        builder = ChainFlowBuilder()
        first = builder.add_stage(
            _stage("first", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATION_COMPLETE),
        )
        second = builder.add_stage(
            _stage("second", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.POST_PROCESSING_COMPLETE),
        )
        builder.connect(first, second)
        with pytest.raises(ChainFlowValidationError, match="share entry progress"):
            builder.build()

    def test_identical_stage_boundaries_rejected(self) -> None:
        """A stage cannot enter and complete on the same progress state."""
        with pytest.raises(ValueError, match="identical entry and completion"):
            _stage("bad", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATING)

    def test_handles_resolve(self) -> None:
        """Handles round-trip through name lookup and node resolution."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        handle = flow.get_node_handle(POST_PROCESS_STAGE_NAME)
        assert handle == ChainNodeHandle(name=POST_PROCESS_STAGE_NAME)
        assert flow.get_node(handle).kind == CHAIN_NODE_KIND.POST_PROCESS
        with pytest.raises(KeyError):
            flow.get_node_handle("nonexistent")


class TestCommonFlows:
    """Shapes of the canonical flows."""

    def test_full_image_flow_shape(self) -> None:
        """The full image flow runs generate -> post_process -> safety_check -> submit."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        assert [node.name for node in flow.nodes] == [
            GENERATE_STAGE_NAME,
            POST_PROCESS_STAGE_NAME,
            SAFETY_CHECK_STAGE_NAME,
            SUBMIT_STAGE_NAME,
        ]
        assert flow.source_handle.name == GENERATE_STAGE_NAME

    def test_minimal_image_flow_shape(self) -> None:
        """Without post-processing, safety, or submit, only the generate stage remains."""
        flow = image_generation_flow(post_processing=False, safety_check=False, submit=False)
        assert [node.name for node in flow.nodes] == [GENERATE_STAGE_NAME]

    def test_alchemy_flow_shape(self) -> None:
        """The alchemy flow starts at post-processing."""
        flow = alchemy_flow()
        assert [node.name for node in flow.nodes] == [POST_PROCESS_STAGE_NAME, SUBMIT_STAGE_NAME]

    def test_text_flow_shape(self) -> None:
        """The text flow runs generate -> submit by default."""
        flow = text_generation_flow()
        assert [node.name for node in flow.nodes] == [GENERATE_STAGE_NAME, SUBMIT_STAGE_NAME]

    def test_capabilities_assigned(self) -> None:
        """Stages carry the lane capabilities workers route on."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        capability_by_name = {node.name: node.required_capability for node in flow.nodes}
        assert capability_by_name == {
            GENERATE_STAGE_NAME: CHAIN_CAPABILITY.INFERENCE,
            POST_PROCESS_STAGE_NAME: CHAIN_CAPABILITY.POST_PROCESSING,
            SAFETY_CHECK_STAGE_NAME: CHAIN_CAPABILITY.SAFETY,
            SUBMIT_STAGE_NAME: None,
        }


class TestChainExecutionContext:
    """The per-unit-of-work state machine."""

    def test_progress_driven_walk(self) -> None:
        """advance_for_progress drives the full image flow from generation progress alone."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        context = ChainExecutionContext(flow)

        generate = flow.get_node_handle(GENERATE_STAGE_NAME)
        post_process = flow.get_node_handle(POST_PROCESS_STAGE_NAME)
        safety = flow.get_node_handle(SAFETY_CHECK_STAGE_NAME)
        submit = flow.get_node_handle(SUBMIT_STAGE_NAME)

        assert context.ready_nodes() == (generate,)

        context.advance_for_progress(GENERATION_PROGRESS.GENERATING)
        assert context.node_state(generate) == CHAIN_NODE_STATE.EXECUTING

        newly_ready = context.advance_for_progress(GENERATION_PROGRESS.GENERATION_COMPLETE)
        assert newly_ready == (post_process,)
        assert context.node_state(generate) == CHAIN_NODE_STATE.COMPLETED

        context.advance_for_progress(GENERATION_PROGRESS.POST_PROCESSING)
        newly_ready = context.advance_for_progress(GENERATION_PROGRESS.POST_PROCESSING_COMPLETE)
        assert newly_ready == (safety,)

        context.advance_for_progress(GENERATION_PROGRESS.SAFETY_CHECKING)
        newly_ready = context.advance_for_progress(GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE)
        assert newly_ready == (submit,)

        context.advance_for_progress(GENERATION_PROGRESS.SUBMITTING)
        context.advance_for_progress(GENERATION_PROGRESS.SUBMIT_COMPLETE)

        assert context.is_finished
        assert not context.has_failed
        assert all(state == CHAIN_NODE_STATE.COMPLETED for state in context.snapshot().values())

    def test_unmapped_progress_is_ignored(self) -> None:
        """Progress values that are not stage boundaries do not move the chain."""
        flow = image_generation_flow(post_processing=False, safety_check=True)
        context = ChainExecutionContext(flow)

        assert context.advance_for_progress(GENERATION_PROGRESS.PRELOADING) == ()
        assert context.advance_for_progress(GENERATION_PROGRESS.PENDING_SAFETY_CHECK) == ()
        assert context.snapshot()[GENERATE_STAGE_NAME] == CHAIN_NODE_STATE.PENDING

    def test_terminal_failure_fails_executing_node_and_skips_downstream(self) -> None:
        """A terminal failure progress fails the executing stage and skips its descendants."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        context = ChainExecutionContext(flow)

        context.advance_for_progress(GENERATION_PROGRESS.GENERATING)
        context.advance_for_progress(GENERATION_PROGRESS.ABORTED)

        snapshot = context.snapshot()
        assert snapshot[GENERATE_STAGE_NAME] == CHAIN_NODE_STATE.FAILED
        assert snapshot[POST_PROCESS_STAGE_NAME] == CHAIN_NODE_STATE.SKIPPED
        assert snapshot[SAFETY_CHECK_STAGE_NAME] == CHAIN_NODE_STATE.SKIPPED
        assert snapshot[SUBMIT_STAGE_NAME] == CHAIN_NODE_STATE.SKIPPED
        assert context.is_finished
        assert context.has_failed
        assert context.node_errors(flow.get_node_handle(GENERATE_STAGE_NAME))

    def test_required_dependency_violation_raises(self) -> None:
        """Starting a stage whose required predecessor has not finished is a consistency error."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        context = ChainExecutionContext(flow)

        with pytest.raises(ChainConsistencyError, match="required predecessor"):
            context.mark_executing(flow.get_node_handle(POST_PROCESS_STAGE_NAME))

    def test_optional_stage_bypassed_implicitly(self) -> None:
        """An optional pending predecessor is skipped when a later stage starts."""
        builder = ChainFlowBuilder()
        first = builder.add_stage(
            _stage("first", GENERATION_PROGRESS.GENERATING, GENERATION_PROGRESS.GENERATION_COMPLETE),
        )
        middle = builder.add_stage(
            _stage(
                "middle",
                GENERATION_PROGRESS.POST_PROCESSING,
                GENERATION_PROGRESS.POST_PROCESSING_COMPLETE,
                optional=True,
            ),
        )
        last = builder.add_stage(
            _stage("last", GENERATION_PROGRESS.SAFETY_CHECKING, GENERATION_PROGRESS.SAFETY_CHECK_COMPLETE),
        )
        builder.connect(first, middle)
        builder.connect(middle, last)
        flow = builder.build()

        context = ChainExecutionContext(flow)
        context.advance_for_progress(GENERATION_PROGRESS.GENERATING)
        context.advance_for_progress(GENERATION_PROGRESS.GENERATION_COMPLETE)
        context.advance_for_progress(GENERATION_PROGRESS.SAFETY_CHECKING)

        snapshot = context.snapshot()
        assert snapshot["middle"] == CHAIN_NODE_STATE.SKIPPED
        assert snapshot["last"] == CHAIN_NODE_STATE.EXECUTING

    def test_explicit_skip_requires_optional(self) -> None:
        """Only optional stages may be skipped explicitly."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        context = ChainExecutionContext(flow)
        with pytest.raises(ChainConsistencyError, match="required"):
            context.mark_skipped(flow.get_node_handle(POST_PROCESS_STAGE_NAME))

    def test_thread_safe_progress_reports(self) -> None:
        """Concurrent advance_for_progress calls do not corrupt state."""
        flow = image_generation_flow(post_processing=False, safety_check=False, submit=False)
        context = ChainExecutionContext(flow)

        context.advance_for_progress(GENERATION_PROGRESS.GENERATING)

        completions = [GENERATION_PROGRESS.GENERATION_COMPLETE] * 8
        threads = [threading.Thread(target=context.advance_for_progress, args=(progress,)) for progress in completions]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert context.snapshot()[GENERATE_STAGE_NAME] == CHAIN_NODE_STATE.COMPLETED


class TestGenerationParity:
    """A real generation's progress history drives the chain to the same conclusion."""

    def test_image_generation_with_post_processing_drives_chain(
        self,
        simple_image_generation_parameters_post_processing: ImageGenerationParameters,
        default_testing_image_bytes: bytes,
    ) -> None:
        """Replaying an actual generation walk through advance_for_progress completes the matching flow."""
        generation = ImageSingleGeneration(
            generation_parameters=simple_image_generation_parameters_post_processing,
        )
        flow = image_generation_flow(
            post_processing=generation.requires_post_processing,
            safety_check=generation.requires_safety_check,
            submit=generation.requires_submit,
        )
        context = ChainExecutionContext(flow)

        generation.on_preloading()
        generation.on_preloading_complete()
        generation.on_generating()
        generation.on_generation_work_complete(default_testing_image_bytes)
        generation.on_post_processing()
        generation.on_post_processing_complete(default_testing_image_bytes + b"-pp")
        generation.on_safety_checking()
        generation.on_safety_check_complete(
            batch_index=0,
            safety_result=ImageSafetyResult(is_nsfw=False, is_csam=False),
        )
        generation.on_submitting()
        generation.on_submit_complete()
        generation.on_complete()

        for progress, _ in generation.get_progress_history():
            context.advance_for_progress(progress)

        assert context.is_finished
        assert not context.has_failed


class TestLocalChainExecutor:
    """The synchronous reference executor."""

    def test_happy_path(self) -> None:
        """All stages complete when work reaches each completion progress."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        executed: list[str] = []

        def work(node: ChainStageNode) -> GENERATION_PROGRESS:
            executed.append(node.name)
            return node.completion_progress

        context = LocalChainExecutor().execute(flow, work)
        assert executed == [
            GENERATE_STAGE_NAME,
            POST_PROCESS_STAGE_NAME,
            SAFETY_CHECK_STAGE_NAME,
            SUBMIT_STAGE_NAME,
        ]
        assert context.is_finished
        assert not context.has_failed

    def test_failure_skips_downstream(self) -> None:
        """A stage that fails prevents downstream stages from executing."""
        flow = image_generation_flow(post_processing=True, safety_check=True)
        executed: list[str] = []

        def work(node: ChainStageNode) -> GENERATION_PROGRESS:
            executed.append(node.name)
            if node.name == POST_PROCESS_STAGE_NAME:
                return GENERATION_PROGRESS.ABORTED
            return node.completion_progress

        context = LocalChainExecutor().execute(flow, work)
        assert executed == [GENERATE_STAGE_NAME, POST_PROCESS_STAGE_NAME]
        snapshot = context.snapshot()
        assert snapshot[POST_PROCESS_STAGE_NAME] == CHAIN_NODE_STATE.FAILED
        assert snapshot[SAFETY_CHECK_STAGE_NAME] == CHAIN_NODE_STATE.SKIPPED
        assert snapshot[SUBMIT_STAGE_NAME] == CHAIN_NODE_STATE.SKIPPED
        assert context.has_failed
