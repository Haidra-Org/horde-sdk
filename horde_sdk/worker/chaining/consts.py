"""Constants for the worker chaining system.

The chaining system describes a unit of work as a directed acyclic graph of stages. It is descriptive rather than
prescriptive: a worker's own orchestration remains the executor of record and drives the chain state from
generation-progress milestones, while simple consumers can use the reference executor in
`horde_sdk.worker.chaining.executors`.
"""

from __future__ import annotations

from enum import auto

from strenum import StrEnum


class CHAIN_NODE_KIND(StrEnum):
    """The kind of work a chain node represents."""

    GENERATE = auto()
    """A round of inference or other primary computation."""

    POST_PROCESS = auto()
    """Post-processing of a previous stage's output (e.g., upscaling or face fixing)."""

    SAFETY_CHECK = auto()
    """A safety evaluation of a previous stage's output."""

    SUBMIT = auto()
    """Delivery of the finished results to the dispatch source."""

    CUSTOM = auto()
    """A custom stage not otherwise classified."""


class CHAIN_NODE_STATE(StrEnum):
    """The execution state of a chain node."""

    PENDING = auto()
    """The node has unmet dependencies and cannot start yet."""

    READY = auto()
    """All dependencies are met; the node is eligible to start."""

    EXECUTING = auto()
    """The node's work is in progress."""

    COMPLETED = auto()
    """The node's work finished successfully."""

    FAILED = auto()
    """The node's work failed terminally."""

    SKIPPED = auto()
    """The node was not executed, either because it is optional or because a dependency failed."""


class CHAIN_CAPABILITY(StrEnum):
    """The lane capability a chain node requires from the executing worker.

    Workers map these tokens onto their own process lanes; the SDK attaches no scheduling semantics to them.
    """

    INFERENCE = auto()
    """Requires a process holding the primary (e.g., checkpoint-loaded) inference backend."""

    POST_PROCESSING = auto()
    """Requires a process holding post-processing models (upscalers, facefixers, background removal)."""

    SAFETY = auto()
    """Requires a process holding the safety evaluation stack."""

    CUSTOM = auto()
    """Requires a worker-defined capability outside the standard set."""


class CHAIN_EDGE_KIND(StrEnum):
    """The known chain edges."""

    CUSTOM = auto()
    """A custom chain edge."""

    SAME_GENERATION = auto()
    """The same generation object flows from one stage to the next within a single unit of work."""

    RESULTING_IMAGE_AS_SOURCE = auto()
    """The resulting image of the previous generation is used as the source for the next generation."""

    RESULTING_TEXT_AS_PROMPT = auto()
    """The resulting text of the previous generation is used as the prompt for the next generation."""

    RESULTING_IMAGE_AS_MASK = auto()
    """The resulting image of the previous generation is used as the mask for the next generation."""

    RESULTING_IMAGE_AS_CONTROL_MAP = auto()
    """The resulting image of the previous generation is used as the control map for the next generation."""

    IMAGE_TO_ALCHEMY_UPSCALE = auto()
    """The resulting image from image generation is used as the source for alchemy upscaling."""

    IMAGE_TO_ALCHEMY_FACEFIX = auto()
    """The resulting image from image generation is used as the source for alchemy face fixing."""

    ALCHEMY_TO_ALCHEMY = auto()
    """The resulting image from one alchemy operation is used as the source for another alchemy operation."""

    TEXT_TO_IMAGE_PROMPT = auto()
    """The resulting text from text generation is used as the prompt for image generation."""
