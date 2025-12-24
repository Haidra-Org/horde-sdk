"""Contains the Alchemy parameters models and related classes.

See :class:`horde_sdk.generation_parameters.alchemy.object_models.AlchemyParameters` for the main
Alchemy parameters model.
"""

from horde_sdk.generation_parameters.alchemy.object_models import (
    AlchemyParameters,
    CaptionAlchemyParameters,
    FacefixAlchemyParameters,
    InterrogateAlchemyParameters,
    NSFWAlchemyParameters,
    ResolverRule,
    SingleAlchemyParameters,
    UpscaleAlchemyParameters,
    instantiate_alchemy_parameters,
    register_alchemy_parameter_rule,
    resolve_alchemy_parameter_model,
    unregister_alchemy_parameter_rule,
)

__all__ = [
    "AlchemyParameters",
    "CaptionAlchemyParameters",
    "FacefixAlchemyParameters",
    "InterrogateAlchemyParameters",
    "NSFWAlchemyParameters",
    "ResolverRule",
    "SingleAlchemyParameters",
    "UpscaleAlchemyParameters",
    "instantiate_alchemy_parameters",
    "register_alchemy_parameter_rule",
    "resolve_alchemy_parameter_model",
    "unregister_alchemy_parameter_rule",
]
