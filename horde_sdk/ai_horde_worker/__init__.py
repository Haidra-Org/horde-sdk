"""Helper methods for creating a worker for the AI Horde."""

from horde_sdk.ai_horde_worker.generations import AlchemySingleGeneration, ImageSingleGeneration, TextSingleGeneration
from horde_sdk.ai_horde_worker.generations_base import HordeSingleGeneration

AnyGenerationType = ImageSingleGeneration | AlchemySingleGeneration | TextSingleGeneration
"""All of the possible generation types."""

from horde_sdk.ai_horde_worker.job_base import HordeWorkerJob, HordeWorkerJobConfig, SingleGenerationTypeVar
from horde_sdk.ai_horde_worker.jobs import AlchemyWorkerJob, ImageWorkerJob, TextWorkerJob

AnyWorkerJobType = ImageWorkerJob | AlchemyWorkerJob | TextWorkerJob

__all__ = [
    "AnyGenerationType",
    "AnyWorkerJobType",
    "HordeSingleGeneration",
    "HordeWorkerJob",
    "HordeWorkerJobConfig",
    "SingleGenerationTypeVar",
    "AlchemySingleGeneration",
    "ImageSingleGeneration",
    "TextSingleGeneration",
    "AlchemyWorkerJob",
    "ImageWorkerJob",
    "TextWorkerJob",
]
