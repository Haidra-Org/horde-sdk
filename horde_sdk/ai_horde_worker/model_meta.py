import os
import re

from horde_model_reference.meta_consts import MODEL_REFERENCE_CATEGORY, STABLE_DIFFUSION_BASELINE_CATEGORY
from horde_model_reference.model_reference_manager import ModelReferenceManager
from horde_model_reference.model_reference_records import StableDiffusion_ModelRecord
from loguru import logger

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageStatsModelsRequest, ImageStatsModelsResponse, StatsModelsTimeframe
from horde_sdk.ai_horde_worker.bridge_data import MetaInstruction
from horde_sdk.generic_api.apimodels import RequestErrorResponse


class ImageModelLoadResolver:
    """Resolve meta instructions for loading models."""

    # set a default timeframe for model stats
    default_timeframe = StatsModelsTimeframe.month

    _model_reference_manager: ModelReferenceManager

    def __init__(self, model_reference_manager: ModelReferenceManager) -> None:  # noqa: D107
        if not isinstance(model_reference_manager, ModelReferenceManager):
            raise TypeError("model_reference_manager must be of type ModelReferenceManager")
        self._model_reference_manager = model_reference_manager

    def resolve_meta_instructions(
        self,
        possible_meta_instructions: list[str],
        client: AIHordeAPIManualClient,
    ) -> set[str]:
        """Return a set of model names based on the given meta instructions.

        Args:
            possible_meta_instructions: A list of strings representing meta instructions.
            client: An AIHordeAPIManualClient object to use for making requests.

        Returns:
            A set of strings representing the names of models to load.
        """
        # Get model stats from the API
        stats_response = client.submit_request(ImageStatsModelsRequest(), ImageStatsModelsResponse)
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

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_SDXL_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_models_of_baseline("stable_diffusion_xl"))

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_SD15_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_models_of_baseline("stable_diffusion_1"))

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_SD21_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_models_of_baseline("stable_diffusion_2_512"))
                return_list.extend(self.resolve_all_models_of_baseline("stable_diffusion_2_768"))

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_INPAINTING_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_inpainting_models())

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_SFW_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_sfw_model_names())

            if ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.ALL_NSFW_REGEX,
                possible_instruction,
            ):
                return_list.extend(self.resolve_all_nsfw_model_names())

        # If no valid meta instruction were found, return None
        return self.remove_large_models(set(return_list))

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

    def remove_large_models(self, models: set[str]) -> set[str]:
        """Remove large models from the input set of models."""
        AI_HORDE_MODEL_META_LARGE_MODELS = os.getenv("AI_HORDE_MODEL_META_LARGE_MODELS")
        if not AI_HORDE_MODEL_META_LARGE_MODELS:
            cascade_models = self.resolve_all_models_of_baseline(STABLE_DIFFUSION_BASELINE_CATEGORY.stable_cascade)
            flux_models = self.resolve_all_models_of_baseline(STABLE_DIFFUSION_BASELINE_CATEGORY.flux_1)

            logger.debug(f"Removing cascade models: {cascade_models}")
            logger.debug(f"Removing flux models: {flux_models}")
            models = models - cascade_models - flux_models
        return models

    def resolve_all_model_names(self) -> set[str]:
        """Get the names of all models defined in the model reference.

        Returns:
            A set of strings representing the names of all models.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        sd_model_references = all_model_references[MODEL_REFERENCE_CATEGORY.stable_diffusion]

        all_models = set(sd_model_references.root.keys()) if sd_model_references is not None else set()

        all_models = self.remove_large_models(all_models)

        if not all_models:
            logger.error("No stable diffusion models found in model reference.")
        return all_models

    def _resolve_sfw_nsfw_model_names(self, nsfw: bool) -> set[str]:
        """Get the names of all SFW or NSFW models defined in the model reference.

        Args:
            nsfw: A boolean representing whether to get SFW or NSFW models.

        Returns:
            A set of strings representing the names of all SFW or NSFW models.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        sd_model_references = all_model_references[MODEL_REFERENCE_CATEGORY.stable_diffusion]

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model in sd_model_references.root.values():
            if not isinstance(model, StableDiffusion_ModelRecord):
                logger.error(f"Model {model} is not a StableDiffusion_ModelRecord")
                continue

            if model.nsfw == nsfw:
                found_models.add(model.name)

        return found_models

    def resolve_all_sfw_model_names(self) -> set[str]:
        """Get the names of all SFW models defined in the model reference.

        Returns:
            A set of strings representing the names of all SFW models.
        """
        return self._resolve_sfw_nsfw_model_names(nsfw=False)

    def resolve_all_nsfw_model_names(self) -> set[str]:
        """Get the names of all NSFW models defined in the model reference.

        Returns:
            A set of strings representing the names of all NSFW models.
        """
        return self._resolve_sfw_nsfw_model_names(nsfw=True)

    def resolve_all_inpainting_models(self) -> set[str]:
        """Get the names of all inpainting models defined in the model reference.

        Returns:
            A set of strings representing the names of all inpainting models.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        sd_model_references = all_model_references[MODEL_REFERENCE_CATEGORY.stable_diffusion]

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model in sd_model_references.root.values():
            if not isinstance(model, StableDiffusion_ModelRecord):
                logger.error(f"Model {model} is not a StableDiffusion_ModelRecord")
                continue

            if model.inpainting:
                found_models.add(model.name)

        return found_models

    def resolve_all_models_of_baseline(self, baseline: str) -> set[str]:
        """Get the names of all models of a given baseline defined in the model reference.

        Args:
            baseline: A string representing the baseline to get models for.

        Returns:
            A set of strings representing the names of all models of the given baseline.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        sd_model_references = all_model_references[MODEL_REFERENCE_CATEGORY.stable_diffusion]

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model in sd_model_references.root.values():
            if not isinstance(model, StableDiffusion_ModelRecord):
                logger.error(f"Model {model} is not a StableDiffusion_ModelRecord")
                continue

            if model.baseline == baseline:
                found_models.add(model.name)

        return found_models

    @staticmethod
    def resolve_top_n_model_names(
        number_of_top_models: int,
        response: ImageStatsModelsResponse,
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
        response: ImageStatsModelsResponse,
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
