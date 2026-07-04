"""Chain node definitions.

A stage node is one step of a unit of work: it names the kind of work, the lane capability it requires, and the
generation-progress states that mark the stage starting and finishing. One generation object flows through all of
the stage nodes of its chain; the generation's progress is the odometer and the chain is the routing plan.
"""

from __future__ import annotations

from dataclasses import dataclass

from horde_sdk.worker.chaining.consts import CHAIN_CAPABILITY, CHAIN_NODE_KIND
from horde_sdk.worker.consts import GENERATION_PROGRESS


@dataclass(frozen=True)
class ChainNodeHandle:
    """An opaque, hashable reference to a node within a chain flow."""

    name: str
    """The unique (within a flow) name of the node this handle refers to."""

    def __str__(self) -> str:
        """Return the node name."""
        return self.name


@dataclass(frozen=True)
class ChainStageNode:
    """A stage of a unit of work, bound to a lane capability.

    Stage completion is defined as the generation reaching `completion_progress`; the stage is considered started
    when the generation reaches `entry_progress`.
    """

    name: str
    """The unique (within a flow) name of the stage."""

    kind: CHAIN_NODE_KIND
    """The kind of work this stage represents."""

    entry_progress: GENERATION_PROGRESS
    """The generation progress value that marks this stage as executing."""

    completion_progress: GENERATION_PROGRESS
    """The generation progress milestone that marks this stage as completed."""

    required_capability: CHAIN_CAPABILITY | None = None
    """The lane capability required to execute this stage, or None when the orchestrating process handles it."""

    optional: bool = False
    """Whether the stage may be skipped without failing the chain."""

    def __post_init__(self) -> None:
        """Validate the node definition.

        Raises:
            ValueError: If the name is empty or entry and completion progress are the same state.
        """
        if not self.name:
            raise ValueError("A chain stage node requires a non-empty name")
        if self.entry_progress == self.completion_progress:
            raise ValueError(
                f"Stage '{self.name}' has identical entry and completion progress ({self.entry_progress}); "
                "a stage must move the generation between two distinct states",
            )

    @property
    def handle(self) -> ChainNodeHandle:
        """The handle referring to this node."""
        return ChainNodeHandle(name=self.name)
