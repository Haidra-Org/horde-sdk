"""Chain edge definitions.

Edges connect stage nodes and declare how the output of one stage becomes the input of the next. For stage flows
within a single unit of work the transformation is the identity: the same generation object carries its own
results forward. Semantic edges that build a *new* unit of work from a finished one (e.g., text-to-image prompt
chaining) share this class and override `transform`-style behavior in later phases.
"""

from __future__ import annotations

from dataclasses import dataclass

from horde_sdk.worker.chaining.consts import CHAIN_EDGE_KIND
from horde_sdk.worker.chaining.nodes import ChainNodeHandle
from horde_sdk.worker.consts import GENERATION_PROGRESS


@dataclass(frozen=True)
class ChainEdge:
    """A directed connection between two stage nodes."""

    kind: CHAIN_EDGE_KIND
    """The kind of hand-off this edge represents."""

    source: ChainNodeHandle
    """The node whose completion feeds this edge."""

    target: ChainNodeHandle
    """The node that becomes eligible when this edge fires."""

    def accepts(self, source_progress: GENERATION_PROGRESS) -> bool:
        """Whether the edge may fire given the source stage's generation progress.

        The default edge fires on any non-failing progress; subclasses may narrow this.

        Args:
            source_progress (GENERATION_PROGRESS): The progress reported at the source stage's completion.

        Returns:
            bool: True when the edge may fire.
        """
        return not GENERATION_PROGRESS.is_state_failing(source_progress)
