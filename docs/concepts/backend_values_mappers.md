# Design Document: Implementing a `BackendValuesMapper`

## Overview

The `BackendValuesMapper` is an abstract base class designed to map values between backend representations and SDK representations. This is useful when the backend uses different naming conventions or representations for the same concepts as the SDK. The `ImageBackendValuesMapper` is a concrete implementation of this concept for image-related backends, and it serves as a template for implementing other `BackendValuesMapper` subclasses for image generation backends.

Mappers are used to automatically provide the correct values to backends when using SDK parameter sets.

This document outlines the steps and considerations for implementing a new `BackendValuesMapper` for a specific backend type using the existing `ImageBackendValuesMapper` as a reference, but you should adapt your implementation to the specific needs of your backend.

---

## Key Classes and Concepts

### 1. **Base Class: `BackendValuesMapper`**

- Abstract base class that provides the foundation for all backend mappers.
- Generic over the type of parameter set it maps (`SDKParameterSetTypeVar`).

### 2. **Abstract Image Class: `ImageBackendValuesMapper`**

- Extends `BackendValuesMapper` and specializes it for image-related backends.
- Generic over three types:
    - `BackendSamplersTypeVar`: Enum for backend samplers.
    - `BackendSchedulersTypeVar`: Enum for backend schedulers.
    - `BackendControlnetsTypeVar`: Enum for backend controlnets.

### 3. **Mapping Logic**

- Maps backend values to SDK values and vice versa using dictionaries.
- Provides validation methods to check if a value is valid for a given type.

---

## Steps to Implement a New `BackendValuesMapper`

### Step 1: Define the Backend-Specific Enums

Create enums for the backend-specific representations of the values you want to map. These enums should inherit from `StrEnum` to ensure compatibility with the existing mapping logic.

```python
from enum import auto()
from strenum import StrEnum

class KNOWN_EXAMPLE_BACKEND_SAMPLERS(StrEnum):
    sampler_a = auto()
    sampler_b = "sampler_b_name_changed" # Keep enum field the same and update the value as a string if the backend changes

class KNOWN_EXAMPLE_BACKEND_SCHEDULERS(StrEnum):
    scheduler_x = auto()
    scheduler_y = auto()

class KNOWN_EXAMPLE_BACKEND_CONTROLNETS(StrEnum):
    controlnet_1 = auto()
    controlnet_2 = auto()
```

If your backend uses the SDK values (and they map 1:1), you should define the enums in the following way:

```python
from horde_sdk.generation_parameters.image.consts import KNOWN_IMAGE_SAMPLERS, KNOWN_IMAGE_SCHEDULERS, KNOWN_IMAGE_CONTROLNETS

KNOWN_EXAMPLE_BACKEND_SAMPLERS = KNOWN_IMAGE_SAMPLERS
KNOWN_EXAMPLE_BACKEND_SCHEDULERS = KNOWN_IMAGE_SCHEDULERS
KNOWN_EXAMPLE_BACKEND_CONTROLNETS = KNOWN_IMAGE_CONTROLNETS
```

... effectively aliasing the SDK enums. This allows later changes to the SDK enums to be reflected while keeping the possibility of having backend-specific values later on.

---

### Step 2: Implement the Concrete Mapper Class

Create a concrete implementation of `BackendValuesMapper`. This class should inherit from `BackendValuesMapper` and specialize it for the backend-specific enums.

Be sure to define dictionaries to map backend values to SDK values and vice versa, preferable as members of your implementing class. These mappings should be comprehensive and account for all known values.

> Note: The use of `ClassVar` is required if you make the mapping dictionaries class members. You can alternatively define them as instance members in the `__init__` method, though that would be marginally less efficient

```python
from typing_extensions import ClassVar
from horde_sdk.backend_parsing.object_models import ImageBackendValuesMapper

class ExampleBackendValuesMapper(
    ImageBackendValuesMapper[
        KNOWN_EXAMPLE_BACKEND_SAMPLERS,
        KNOWN_EXAMPLE_BACKEND_SCHEDULERS,
        KNOWN_EXAMPLE_BACKEND_CONTROLNETS,
    ],
):
    """Mapper for Custom Backend values."""

    _EXAMPLE_BACKEND_SAMPLERS_CONVERT_MAP: ClassVar[dict[KNOWN_EXAMPLE_BACKEND_SAMPLERS | str, KNOWN_IMAGE_SAMPLERS]] = {
        KNOWN_EXAMPLE_BACKEND_SAMPLERS.sampler_a: KNOWN_IMAGE_SAMPLERS.k_euler,
        KNOWN_EXAMPLE_BACKEND_SAMPLERS.sampler_b: KNOWN_IMAGE_SAMPLERS.k_lms,
    }
    _EXAMPLE_BACKEND_SCHEDULERS_CONVERT_MAP: ClassVar[dict[KNOWN_EXAMPLE_BACKEND_SCHEDULERS | str, KNOWN_IMAGE_SCHEDULERS]] = {
        KNOWN_EXAMPLE_BACKEND_SCHEDULERS.scheduler_x: KNOWN_IMAGE_SCHEDULERS.k_dpm_2,
        KNOWN_EXAMPLE_BACKEND_SCHEDULERS.scheduler_y: KNOWN_IMAGE_SCHEDULERS.k_dpmpp_sde,
    }
    _EXAMPLE_BACKEND_CONTROLNETS_CONVERT_MAP: ClassVar[dict[KNOWN_EXAMPLE_BACKEND_CONTROLNETS | str, KNOWN_IMAGE_CONTROLNETS]] = {
        KNOWN_EXAMPLE_BACKEND_CONTROLNETS.controlnet_1: KNOWN_IMAGE_CONTROLNETS.canny,
        KNOWN_EXAMPLE_BACKEND_CONTROLNETS.controlnet_2: KNOWN_IMAGE_CONTROLNETS.depth,
    }

    def __init__(self) -> None:
        super().__init__(
            backend_samplers_type=KNOWN_EXAMPLE_BACKEND_SAMPLERS,
            backend_schedulers_type=KNOWN_EXAMPLE_BACKEND_SCHEDULERS,
            backend_controlnets_type=KNOWN_EXAMPLE_BACKEND_CONTROLNETS,
            sdk_samplers_map=self._EXAMPLE_BACKEND_SAMPLERS_CONVERT_MAP,
            sdk_schedulers_map=self._EXAMPLE_BACKEND_SCHEDULERS_CONVERT_MAP,
            sdk_controlnets_map=self._EXAMPLE_BACKEND_CONTROLNETS_CONVERT_MAP,
        )
```

---

### Step 3: Add Mapping Methods (if not already provided)

If additional mapping logic is required, you should implement the necessary methods in your concrete mapper class. This may include methods for validating values, converting between backend and SDK representations, and any other specific logic required by your backend.

`ImageBackendValuesMapper` already provides image generation-specific mappings, but you may need to implement additional methods for your backend.

```python
def map_to_sdk_sampler(self, backend_sampler: KNOWN_EXAMPLE_BACKEND_SAMPLERS) -> KNOWN_IMAGE_SAMPLERS:
    """Maps a backend sampler to an SDK sampler."""
    ...

def map_to_example_backend_sampler(self, sdk_sampler: KNOWN_IMAGE_SAMPLERS) -> KNOWN_EXAMPLE_BACKEND_SAMPLERS:
    """Maps an SDK sampler to a backend sampler."""
    ...

...
```

#### Understanding `_map_value` and `_is_valid_value`

The `BackendValuesMapper` base class provides two utility methods, `_map_value` and `_is_valid_value`, which can be leveraged when implementing your custom mapper. These functions help work the the `StrEnum` based types for the backend and SDK values.

- **`_map_value`**:
    - This method handles the conversion of a value from one representation to another using a mapping dictionary.
    - It supports both `StrEnum` and `str` types for input and output, ensuring flexibility in mapping.
    - If the mapping dictionary is empty, it defaults to converting the value based on the target type's members.
    - It is a generic function and provides static (and runtime, where appropriate) type checking for the input and output types.
    - Example usage:

      ```python
      def map_to_sdk_sampler(self, backend_sampler: BackendSamplersTypeVar | str) -> KNOWN_IMAGE_SAMPLERS:
          return self._map_value(
              value=backend_sampler,
              mapping=self._to_sdk_sampler_map,
              known_input_type=self._backend_samplers_type,
              known_target_type=KNOWN_IMAGE_SAMPLERS,
          )
      ```

- **`_is_valid_value`**:
    - This method checks if a given value is valid for a specific `StrEnum` type.
    - It validates both `StrEnum` and `str` inputs by checking against the enum's members and their values.
    - Example usage:

      ```python
      def is_valid_backend_sampler(self, backend_sampler: BackendSamplersTypeVar | str) -> bool:
          return self._is_valid_value(
              value=backend_sampler,
              known_type=self._backend_samplers_type,
          )
      ```

See the `ImageBackendValuesMapper` class for a complete example of how these methods are used.

---

### Step 4: Write Unit Tests

Ensure the mapper works as expected by writing unit tests for all mapping methods.

```python
def test_map_to_sdk_sampler():
    mapper = CustomBackendValuesMapper()
    assert mapper.map_to_sdk_sampler(KNOWN_EXAMPLE_BACKEND_SAMPLERS.sampler_a) == KNOWN_IMAGE_SAMPLERS.k_euler

def test_map_to_EXAMPLE_BACKEND_sampler():
    mapper = CustomBackendValuesMapper()
    assert mapper.map_to_EXAMPLE_BACKEND_sampler(KNOWN_IMAGE_SAMPLERS.k_euler) == KNOWN_EXAMPLE_BACKEND_SAMPLERS.sampler_a
```

---

## Example Usage

```python
mapper = CustomBackendValuesMapper()

# Map backend sampler to SDK sampler
sdk_sampler = mapper.map_to_sdk_sampler(KNOWN_EXAMPLE_BACKEND_SAMPLERS.sampler_a)

# Map SDK sampler to backend sampler
backend_sampler = mapper.map_to_EXAMPLE_BACKEND_sampler(KNOWN_IMAGE_SAMPLERS.k_euler)

# Validate backend sampler
is_valid = mapper.is_valid_EXAMPLE_BACKEND_sampler("sampler_a")
```

---
