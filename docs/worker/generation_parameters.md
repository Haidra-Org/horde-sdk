# Generation Parameters

In `horde-sdk`, **generation parameters** are structured objects that define the configuration and options for a single round of inference or post-processing, such as generating an image or running an alchemy operation. These parameters are designed to be flexible, extensible, and type-safe, supporting a wide variety of generation workflows.

## Object Hierarchy and Template Classes

The generation parameter system is built around a hierarchy of Pydantic models. At the core of this design is the use of **template classes** — base models whose fields are all optional (type hinted in the code as `| None`). These template classes provide a flexible foundation for representing partial or evolving parameter sets. More concrete subclasses then override or specialize these fields, marking them as required or setting defaults as appropriate for specific use cases.

### Why Template Classes?

The primary reason for using template classes is to allow for **partial specification** of parameters. This is specifically required for the "Chain Flows" (dynamic workflows) in the horde-sdk, where it may not be possible to set a given field to a reasonable default ahead of time. For example, "prompt" is always required for image generation, but Chain Flows can be configured to use a prompt generated from a previous step, which may not be known at the time of parameter construction. By using a template class, we can enjoy the flexibility of having all fields optional, while still being able to enforce requirements in concrete subclasses by using Pydantic's validation features.

## Core Classes

### `ComposedParameterSetBase`

This is the base for all classes which contain **all** values required by the backend to execute a generation. These classes may further contain classes which are children of `GenerationParameterComponentBase`, which represent generation components such as LoRas, Controlnets, or other specialized processing steps which are self-contained and have several parameters of their own.

### `GenerationParameterComponentBase`

Implementations of this class represent groups of parameters which pertain to a specific auxiliary processing step or component in the generation workflow. This can include features like LoRas, but may also include back-end specific sets of parameters or groups of closely related parameters. These classes may also be used when a parameter requires a list of a multiple related values.

### `BasicModelGenerationParameters`

A child class of `GenerationParameterComponentBase`, this class is meant to be a base for all model-based generation parameters. It includes fields that are common across different types of generation, such as `model`, `model_baseline`, `model_filename` and `model_hash`. Any generative process that requires a model should inherit from this class to ensure that these common fields are present.

Processes (still called "generations" in the code) that do not require a model

### `BasicImageGenerationParametersTemplate`

This is the template class for image generation parameters. All fields are optional, allowing for flexible construction and partial validation.

> Note: This implementation differs from the actual horde-sdk, and is provided here for illustrative purposes. The actual implementation may have additional fields or different defaults.

```python
class BasicImageGenerationParametersTemplate(BasicModelGenerationParameters):
    prompt: str | None = None
    seed: str | None = None
    height: int | None = Field(default=None, multiple_of=64, ge=64)
    width: int | None = Field(default=None, multiple_of=64, ge=64)
    steps: int | None = Field(default=None, ge=1)
    cfg_scale: float | None = Field(default=None, ge=0)
    sampler_name: KNOWN_IMAGE_SAMPLERS | str | None = Field(default=None)
    scheduler: KNOWN_IMAGE_SCHEDULERS | str | None = Field(default=None)
    clip_skip: int | None = Field(default=None)
    clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = Field(default=None)
    denoising_strength: float | None = Field(default=None, ge=0, le=1)
```

### `BasicImageGenerationParameters`

This is a concrete subclass of the template, making certain fields required and setting sensible defaults. It represents the minimum viable set of parameters for an image generation.

```python
class BasicImageGenerationParameters(BasicImageGenerationParametersTemplate):
    prompt: str
    height: int | None = Field(default=DEFAULT_BASELINE_RESOLUTION, multiple_of=64, ge=64)
    width: int | None = Field(default=DEFAULT_BASELINE_RESOLUTION, multiple_of=64, ge=64)
    clip_skip_representation: CLIP_SKIP_REPRESENTATION | None = Field(default=CLIP_SKIP_REPRESENTATION.NEGATIVE_OFFSET)
```

### 3. Composed and Component Classes

- **ComposedParameterSetBase:** Used for parameter sets that combine multiple components.
- **GenerationParameterComponentBase:** Base class for parameter components (e.g., Controlnet, Remix, HiresFix).

#### Example: Image Generation Parameters

```python
class ImageGenerationParametersTemplate(ComposedParameterSetBase):
    batch_size: int | None = Field(default=None, ge=1)
    tiling: bool | None = None
    source_processing: KNOWN_IMAGE_SOURCE_PROCESSING | str | None = None
    base_params: BasicImageGenerationParameters | None = None
    additional_params: list[GenerationParameterComponentBase] | None = None
    # ...other fields...
```

Concrete implementation:

```python
class ImageGenerationParameters(ImageGenerationParametersTemplate):
    result_ids: list[ID_TYPES]
    base_params: BasicImageGenerationParameters
    batch_size: int | None = Field(default=1, ge=1)
    # ...validators to enforce required fields...
```

## Feature Flags

Feature flags are used to describe the capabilities or requirements of a worker or generation. These are modeled as Pydantic classes, such as:

- `GenerationFeatureFlags` (base)
- `ImageGenerationFeatureFlags` (image-specific)
- `ControlnetFeatureFlags` (controlnet-specific)

These classes help communicate what features are available or required for a given generation.
