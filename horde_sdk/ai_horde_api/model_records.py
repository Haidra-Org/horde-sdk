from typing import override

from horde_model_reference.model_reference_records import GenericModelRecord

from horde_sdk.generation_parameters.generic.object_models import ModelRecordResolver


class AIHordeModelRecordResolver(ModelRecordResolver):
    """Resolver for AI Horde model records."""

    @override
    def resolve_model_by_name(
        self,
        model_name: str,
    ) -> GenericModelRecord | None:
        pass
