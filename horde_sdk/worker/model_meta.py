import os
import re

from horde_model_reference.meta_consts import KNOWN_IMAGE_GENERATION_BASELINE, MODEL_REFERENCE_CATEGORY
from horde_model_reference.model_reference_manager import ModelReferenceManager, PrefetchStrategy
from horde_model_reference.model_reference_records import ImageGenerationModelRecord
from loguru import logger

from horde_sdk.ai_horde_api.ai_horde_clients import AIHordeAPIManualClient
from horde_sdk.ai_horde_api.apimodels import ImageStatsModelsRequest, ImageStatsModelsResponse, StatsModelsTimeframe
from horde_sdk.ai_horde_api.consts import MODEL_STATE
from horde_sdk.generic_api.apimodels import RequestErrorResponse
from horde_sdk.worker.dispatch.ai_horde.bridge_data import MetaInstruction


class ImageModelLoadResolver:
    """Resolve meta instructions for loading models."""

    # set a default timeframe for model stats
    default_timeframe = StatsModelsTimeframe.month

    _model_reference_manager: ModelReferenceManager

    async def _initialize_model_reference_manager(self) -> ModelReferenceManager:
        """Asynchronously initialize the model reference manager."""
        if ModelReferenceManager.has_instance():
            return ModelReferenceManager.get_instance()

        ModelReferenceManager(prefetch_strategy=PrefetchStrategy.ASYNC)
        handle = ModelReferenceManager.get_instance().deferred_prefetch_handle
        if not handle:
            raise Exception(
                "ModelReferenceManager instance was not properly initialized with a deferred prefetch handle."
            )

        await handle

        return ModelReferenceManager.get_instance()

    def __init__(self, model_reference_manager: ModelReferenceManager | None = None) -> None:
        """Initialise the resolver.

        Args:
            model_reference_manager: An already-initialised manager to read the reference from. Inject this
                to reuse a caller-owned manager (for example an offline, disk-only one) instead of having
                the resolver build its own. Reading the reference only needs records already on disk; left
                as ``None`` the resolver constructs a network-fetching manager and awaits its prefetch,
                which blocks the caller on a PRIMARY-API round-trip whose latency it cannot bound. A
                process that must not stall on the network (or that already owns a manager) should pass it.
        """
        # Injected manager: use it as-is and skip all event-loop / network init below.
        if model_reference_manager is not None:
            self._model_reference_manager = model_reference_manager
            return

        import asyncio

        # Check to see if there is already a running asyncio loop, and use that if possible
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                logger.debug("Using existing running event loop to initialize model reference manager.")
                self._model_reference_manager = loop.run_until_complete(self._initialize_model_reference_manager())
            else:
                logger.debug("No running event loop found. Initializing model reference manager with new event loop.")
                self._model_reference_manager = asyncio.run(self._initialize_model_reference_manager())
        except RuntimeError:
            logger.debug("No running event loop found. Initializing model reference manager with new event loop.")
            self._model_reference_manager = asyncio.run(self._initialize_model_reference_manager())

    _cached_stats_response: ImageStatsModelsResponse | None = None

    def _get_stats_response(
        self,
        client: AIHordeAPIManualClient,
        use_cached: bool = False,
    ) -> ImageStatsModelsResponse:
        """Fetch model statistics, optionally reusing the previous resolution's response."""
        if self._cached_stats_response is None or not use_cached:
            response = client.submit_request(
                ImageStatsModelsRequest(model_state=MODEL_STATE.known),
                ImageStatsModelsResponse,
            )
            if isinstance(response, RequestErrorResponse):
                raise Exception(f"Error getting stats for models: {response.message}")
            self._cached_stats_response = response
        return self._cached_stats_response

    def resolve_meta_instructions(
        self,
        possible_meta_instructions: list[str],
        client: AIHordeAPIManualClient,
        *,
        load_large_models: bool = True,
        use_cached_stats_response: bool = False,
    ) -> set[str]:
        """Return a set of model names based on the given meta instructions.

        Args:
            possible_meta_instructions: A list of strings representing meta instructions.
            client: An AIHordeAPIManualClient object to use for making requests.
            load_large_models: A boolean representing whether to load large models. Defaults to True.
            use_cached_stats_response: Whether to use a cached stats response, if available. Defaults to False.

        Returns:
            A set of strings representing the names of models to load.
        """
        return_list: list[str] = []
        stats_response: ImageStatsModelsResponse | None = None

        def get_stats_response() -> ImageStatsModelsResponse:
            """Fetch at most one statistics snapshot for this resolution."""
            nonlocal stats_response
            if stats_response is None:
                stats_response = self._get_stats_response(client, use_cached=use_cached_stats_response)
            return stats_response

        found_top_n = False
        found_bottom_n = False

        for possible_instruction in possible_meta_instructions:
            if ImageModelLoadResolver.meta_instruction_regex_match(MetaInstruction.ALL_REGEX, possible_instruction):
                return self.remove_large_models(set(self.resolve_all_model_names()))

            top_n_newest = ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.NEW_N_REGEX,
                possible_instruction,
            )

            if top_n_newest:
                logger.debug(f"Resolving top {top_n_newest.group(1)} newest models.")
                return_list.extend(
                    self.resolve_newest_n_model_names(
                        number_of_newest_models=int(top_n_newest.group(1)),
                    )
                )
                continue

            top_n_matches = ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.TOP_N_REGEX,
                possible_instruction,
            )
            if top_n_matches:
                return_list.extend(
                    ImageModelLoadResolver.resolve_top_n_model_names(
                        int(top_n_matches.group(1)),
                        get_stats_response(),
                        self.default_timeframe,
                    ),
                )
                if found_top_n:
                    logger.warning("Multiple top N instructions found. This probably isn't intended.")
                found_top_n = True
                continue

            bottom_n_matches = ImageModelLoadResolver.meta_instruction_regex_match(
                MetaInstruction.BOTTOM_N_REGEX,
                possible_instruction,
            )
            if bottom_n_matches:
                return_list.extend(
                    ImageModelLoadResolver.resolve_bottom_n_model_names(
                        int(bottom_n_matches.group(1)),
                        get_stats_response(),
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

        if not load_large_models:
            return self.remove_large_models(set(return_list))

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

    def remove_large_models(
        self,
        models: set[str],
        load_large_models: bool = True,
    ) -> set[str]:
        """Remove large models from the input set of models."""
        AI_HORDE_MODEL_META_LARGE_MODELS = os.getenv("AI_HORDE_MODEL_META_LARGE_MODELS")
        if not AI_HORDE_MODEL_META_LARGE_MODELS or not load_large_models:
            cascade_models = self.resolve_all_models_of_baseline(KNOWN_IMAGE_GENERATION_BASELINE.stable_cascade)
            flux_models = self.resolve_all_models_of_baseline(KNOWN_IMAGE_GENERATION_BASELINE.flux_1)

            if not AI_HORDE_MODEL_META_LARGE_MODELS:
                logger.debug(
                    "Loading of large models is disabled with `AI_HORDE_MODEL_META_LARGE_MODELS`. "
                    f"Removing {len(cascade_models) + len(flux_models)} models. "
                    f"({cascade_models}, {flux_models})",
                )
            models = models - cascade_models - flux_models
        return models

    def resolve_all_model_names(
        self,
        ignore_large_models_env_var: bool = True,
    ) -> set[str]:
        """Get the names of all models defined in the model reference.

        Args:
            ignore_large_models_env_var (bool): A boolean representing whether to ignore the environment variable for
                large models, effectively returning all models regardless of `AI_HORDE_MODEL_META_LARGE_MODELS`.

        Returns:
            A set of strings representing the names of all models.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        # Use .get(), not [...]: a model reference manager may omit a category entirely when its
        # reference failed to load (or simply is not present), not merely map it to None. An absent key
        # would raise KeyError here; .get() yields None, which the guards below already handle.
        sd_model_references = all_model_references.get(MODEL_REFERENCE_CATEGORY.image_generation)

        all_models = set(sd_model_references.keys()) if sd_model_references is not None else set()

        if not ignore_large_models_env_var:
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

        # Use .get(), not [...]: a model reference manager may omit a category entirely when its
        # reference failed to load (or simply is not present), not merely map it to None. An absent key
        # would raise KeyError here; .get() yields None, which the guards below already handle.
        sd_model_references = all_model_references.get(MODEL_REFERENCE_CATEGORY.image_generation)

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model_name, model in sd_model_references.items():
            if not isinstance(model, ImageGenerationModelRecord):
                logger.error(f"Model {model_name} is not a ImageGenerationModelRecord")
                continue

            if model.nsfw == nsfw:
                found_models.add(model_name)

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

        # Use .get(), not [...]: a model reference manager may omit a category entirely when its
        # reference failed to load (or simply is not present), not merely map it to None. An absent key
        # would raise KeyError here; .get() yields None, which the guards below already handle.
        sd_model_references = all_model_references.get(MODEL_REFERENCE_CATEGORY.image_generation)

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model_name, model in sd_model_references.items():
            if not isinstance(model, ImageGenerationModelRecord):
                logger.error(f"Model {model_name} is not a ImageGenerationModelRecord")
                continue

            if model.inpainting:
                found_models.add(model_name)

        return found_models

    def resolve_all_models_of_baseline(self, baseline: str) -> set[str]:
        """Get the names of all models of a given baseline defined in the model reference.

        Args:
            baseline: A string representing the baseline to get models for.

        Returns:
            A set of strings representing the names of all models of the given baseline.
        """
        all_model_references = self._model_reference_manager.get_all_model_references()

        # Use .get(), not [...]: a model reference manager may omit a category entirely when its
        # reference failed to load (or simply is not present), not merely map it to None. An absent key
        # would raise KeyError here; .get() yields None, which the guards below already handle.
        sd_model_references = all_model_references.get(MODEL_REFERENCE_CATEGORY.image_generation)

        found_models: set[str] = set()

        if sd_model_references is None:
            logger.error("No stable diffusion models found in model reference.")
            return found_models

        for model_name, model in sd_model_references.items():
            if not isinstance(model, ImageGenerationModelRecord):
                logger.error(f"Model {model_name} is not a ImageGenerationModelRecord")
                continue

            if model.baseline == baseline:
                found_models.add(model_name)

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

    def resolve_newest_n_model_names(
        self,
        number_of_newest_models: int,
    ) -> list[str]:
        """Get the names of the newest N models based on their creation date.

        Args:
            number_of_newest_models: An integer representing the number of newest models to return.

        Returns:
            A list of strings representing the names of the newest N models.
        """
        try:
            sd_model_reference = self._model_reference_manager.get_model_reference(
                MODEL_REFERENCE_CATEGORY.image_generation
            )
        except Exception as e:
            logger.error(f"Error getting model reference: {e}")
            return []

        if not sd_model_reference:
            return []

        def by_created_at(
            item: tuple[str, ImageGenerationModelRecord],
        ) -> int:
            created_at = item[1].metadata.created_at
            if created_at is None:
                raise ValueError("created_at must be set; sortable is pre-filtered")
            return created_at

        sortable = [
            (name, record) for name, record in sd_model_reference.items() if record.metadata.created_at is not None
        ]
        newest = sorted(sortable, key=by_created_at, reverse=True)[:number_of_newest_models]

        return [record.name for _, record in newest]
