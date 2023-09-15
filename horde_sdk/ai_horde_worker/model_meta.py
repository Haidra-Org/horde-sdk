import re

from horde_model_reference.meta_consts import MODEL_REFERENCE_CATEGORY
from horde_model_reference.model_reference_manager import ModelReferenceManager
from loguru import logger

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import StatsImageModelsRequest, StatsModelsResponse, StatsModelsTimeframe
from horde_sdk.ai_horde_worker.bridge_data import MetaInstruction
from horde_sdk.generic_api.apimodels import RequestErrorResponse


class ImageModelLoadResolver:
    """Resolve meta instructions for loading models."""

    # set a default timeframe for model stats
    default_timeframe = StatsModelsTimeframe.month

    _model_reference_manager: ModelReferenceManager

    def __init__(self, model_reference_manager: ModelReferenceManager) -> None:
        if not isinstance(model_reference_manager, ModelReferenceManager):
            raise TypeError("model_reference_manager must be of type ModelReferenceManager")
        self._model_reference_manager = model_reference_manager

    def resolve_meta_instructions(
        self,
        possible_meta_instructions: list[str],
        client: AIHordeAPIManualClient,
    ) -> set[str]:
        # Get model stats from the API
        stats_response = client.submit_request(StatsImageModelsRequest(), StatsModelsResponse)
        if isinstance(stats_response, RequestErrorResponse):
            raise Exception(f"Error getting stats for models: {stats_response.message}")

        return_list: list[str] = []

        found_top_n = False
        found_bottom_n = False

        # Check each possible meta instruction and return the appropriate model names
        for possible_instruction in possible_meta_instructions:
            # If the instruction is to load all models, return all model names
            if ImageModelLoadResolver.meta_instruction_regex_match(MetaInstruction.ALL_REGEX, possible_instruction):
                return self.resolve_all_model_names()

            # If the instruction is to load the top N models, add the top N model names
            top_n_matches = ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.TOP_N_REGEX,
                possible_instruction,
            )
            if top_n_matches:
                return_list.extend(
                    ImageModelLoadResolver.resolve_top_n_model_names(
                        int(top_n_matches.group(1)),
                        stats_response,
                        self.default_timeframe,
                    ),
                )
                if found_top_n:
                    logger.warning("Multiple top N instructions found. This probably isn't intended.")
                found_top_n = True
                continue

            # If the instruction is to load the bottom N models, add the bottom N model names
            bottom_n_matches = ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.BOTTOM_N_REGEX,
                possible_instruction,
            )
            if bottom_n_matches:
                return_list.extend(
                    ImageModelLoadResolver.resolve_bottom_n_model_names(
                        int(bottom_n_matches.group(1)),
                        stats_response,
                        self.default_timeframe,
                    ),
                )
                if found_bottom_n:
                    logger.warning("Multiple bottom N instructions found. This probably isn't intended.")
                found_bottom_n = True
                continue

        # If no valid meta instruction were found, return None
        return set(return_list)

    @staticmethod
    def meta_instruction_regex_match(instruction: str, target_string: str) -> re.Match[str] | None:
        """Check if a target string matches a given meta instruction regex pattern.

        Args:
            instruction: A string representing the meta instruction regex pattern.
            target_string: The string to check for a match.

        Returns:
            A Match object if the target string matches the regex pattern, otherwise None.
        """
        return re.match(instruction, target_string, re.IGNORECASE)

    def resolve_all_model_names(self) -> set[str]:
        """Get the names of all models defined in the model reference.

        Returns:
            A set of strings representing the names of all models.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        sd_model_references = all_model_references[MODEL_REFERENCE_CATEGORY.stable_diffusion]

        if sd_model_references:
            return set(sd_model_references.root.keys())

        logger.error("No stable diffusion models found in model reference.")
        return set()

    @staticmethod
    def resolve_top_n_model_names(
        number_of_top_models: int,
        response: StatsModelsResponse,
        timeframe: StatsModelsTimeframe,
    ) -> list[str]:
        """Get the names of the top N models based on usage statistics.

        Args:
            number_of_top_models: An integer representing the number of top models to return.
            response: A StatsModelsResponse object containing model usage statistics.
            timeframe: A StatsModelsTimeframe object representing the timeframe to consider.

        Returns:
            A set of strings representing the names of the top N models.
        """
        models_in_timeframe = response.get_timeframe(timeframe)

        # Remove the blank or null values from the dict
        models_in_timeframe = {k: v for k, v in models_in_timeframe.items() if k and v is not None}

        # Sort by value (number of uses) ascending (highest first)
        sorted_models = sorted(models_in_timeframe.items(), key=lambda x: x[1], reverse=True)

        # Get the top n models
        top_n_models = sorted_models[:number_of_top_models]

        # Get just the model names as a list
        return [model[0] for model in top_n_models]

    @staticmethod
    def resolve_bottom_n_model_names(
        number_of_bottom_models: int,
        response: StatsModelsResponse,
        timeframe: StatsModelsTimeframe,
    ) -> list[str]:
        """Get the names of the bottom N models based on usage statistics.

        Args:
            number_of_bottom_models: An integer representing the number of bottom models to return.
            response: A StatsModelsResponse object containing model usage statistics.
            timeframe: A StatsModelsTimeframe object representing the timeframe to consider.

        Returns:
            A set of strings representing the names of the bottom N models.
        """
        models_in_timeframe = response.get_timeframe(timeframe)

        # Remove the blank or null values from the dict
        models_in_timeframe = {k: v for k, v in models_in_timeframe.items() if k and v is not None}

        # Sort by value (number of uses) ascending (lowest first)
        sorted_models = sorted(models_in_timeframe.items(), key=lambda x: x[1])

        # Get the bottom n models
        bottom_n_models = sorted_models[:number_of_bottom_models]

        # Get just the model names as a list
        return [model[0] for model in bottom_n_models]
