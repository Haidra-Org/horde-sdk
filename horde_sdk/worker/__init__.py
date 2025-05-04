"""Helper methods for creating a worker for the AI Horde."""

from horde_sdk.worker.generations import AlchemySingleGeneration, ImageSingleGeneration, TextSingleGeneration
from horde_sdk.worker.generations_base import HordeSingleGeneration

AnyGenerationType = ImageSingleGeneration | AlchemySingleGeneration | TextSingleGeneration
"""All of the possible generation types."""

from horde_sdk.worker.job_base import HordeWorkerJob, HordeWorkerJobConfig, SingleGenerationTypeVar
from horde_sdk.worker.jobs import AlchemyWorkerJob, ImageWorkerJob, TextWorkerJob

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
