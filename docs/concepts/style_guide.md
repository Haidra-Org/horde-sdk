
# Code Philosophy and Design Constraints

## Table of Contents

- [Code Philosophy and Design Constraints](#code-philosophy-and-design-constraints)
    - [Table of Contents](#table-of-contents)
    - [Too long; didn't read](#too-long-didnt-read)
    - [General Principles](#general-principles)
    - [Naming Conventions](#naming-conventions)
        - [Module and Package Naming](#module-and-package-naming)
        - [Variable, Function, Method and Class Naming](#variable-function-method-and-class-naming)
        - [Class Prefixes, Suffixes, and other Naming Conventions](#class-prefixes-suffixes-and-other-naming-conventions)
            - [General](#general)
            - [API/Client Specific](#apiclient-specific)
            - [Generation/Inference Specific](#generationinference-specific)
    - [Error Handling](#error-handling)
    - [Documentation](#documentation)
        - [API Model Specific Documentation](#api-model-specific-documentation)
    - [Function and Method Signatures](#function-and-method-signatures)
    - [Object-Oriented Design](#object-oriented-design)
    - [Method Overloading and Return Types](#method-overloading-and-return-types)
    - [Control Flow and Readability](#control-flow-and-readability)
    - [Data Structures, Models, and Constants](#data-structures-models-and-constants)
        - ["KNOWN" Constants](#known-constants)
    - [Imports and Module Export](#imports-and-module-export)
    - [Pydantic BaseModel Usage](#pydantic-basemodel-usage)
    - [API Model Verification](#api-model-verification)

## Too long; didn't read

If this is your first time contributing, consider this a document to intermittently reference as you work on the codebase rather than a document to memorize. Many of the guidelines are enforced by linting or testing tools, and many of the other rules can be followed by matching the patterns already present in the codebase.

In brief:

- Descriptive, unambiguous naming is required; avoid abbreviations and acronyms unless they are widely understood.
- Never silently handle exceptions; always log or re-raise, and avoid blanket or bare excepts.
- All public APIs must have Google-style docstrings.
- Readability first: Prefer guard clauses, clear control flow, meaningfully named boolean expressions and avoid deeply nested structures.
- Type hints are mandatory for all public functions, methods, class attributes, and module-level variables.
- Code should be written in a way that can be statically analyzed and linted.
    - Avoid (whenever possible) magic strings/numbers and direct dictionary access by key literals.
    - Prefer classes over dictionaries/tuples for data structures.
    - Use `Enum`/`StrEnum` for fixed sets of values.

The principals described in this document are principled and highly opinionated. They exist for the purpose of consistency and strive to improve maintainability. These standards do not purport to be the "best" way and they are not an attack on alternative approaches. Change proposals are welcome to this document if you feel that something is overly restrictive, missing, or could be improved.

## General Principles

- [PEP 20](https://peps.python.org/pep-0020/) should guide code design and implementation.
    - In the case not explicitly covered by these guidelines, the spirit of the principles outlined in PEP 20 should be followed.
- **All** function arguments and return values, class attributes and fields, and module-level variables must be type hinted.
    - See the [mypy type hint cheat sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html) for a primer.
    - Local variables generally only need a type hint if mypy reports an error or warning about them, but it should be considered good practice to type hint them as well.
    - Use Python 3.10+ union types (e.g., `int | str`) instead of `typing.Union[int, str]` and use `| None` for optional types (e.g., `int | None`).

## Naming Conventions

### Module and Package Naming

- Modules and packages should be named using lower snake_case, and should always include an underscore between each significant word or abbreviation.
    - Example module names:
        - `ai_horde_api`
        - `generic_api`
        - `generation_parameters`
- Modules or packages must never be named using a python builtin library name nor should it use the name of a popular third-party library.
    - Example **banned** module names:
        - `logging`
        - `json`
        - `requests`

### Variable, Function, Method and Class Naming

- snake_case must be used for variables, fields, functions, and methods.
    - An underscore must appear between each significant word or abbreviation.
- CamelCase should be used for classes.
- ALL_CAPS_WITH_UNDERSCORES should be used for constants.
- Private variables and methods should be prefixed with a single underscore (e.g., `_private_variable`).
- **Names must be descriptive**
    - This is a firm requirement. Names should be descriptive enough that there is very little room for ambiguity, especially in context or with minimal explanation. This is not always possible to get completely right, but it must be clear that the developer made an effort to do so.
    - One/two/three letter variable names must be avoided unless:
        - They are in a very small scope (e.g., `i` for a loop)
        - In a mathematical context (e.g., `x`, `y`, `z`) where the variables have no significant meaning or are known by convention (the constant `e` for Euler's number).
        - The variable is named this way in an external module or library and the name is being preserved for consistency and clarity.
    - Avoid abbreviations unless they are **widely** understood (e.g., `url`, `api`, `id`, etc.) **and** significantly improve readability
        - For example `img`, `num`, `cnt`, `val`, are not considerably shorter. Writing these out fully improves readability in these cases.
        - "Widely" does not mean "common in some big codebase" or "common in a narrow field". It does mean "common enough that most developers will understand it without needing to look it up".
        - Some acceptable abbreviations include `id`, `db`, `param`, `anon`, and `obj`.
    - Acronyms similarly should be avoided unless they are widely understood and significantly improve readability.
        - For example, `HTTP`, `URL`, `API`, `JSON`, `XML`, `HTML` are acceptable acronyms.
        - Avoid using acronyms that are specific to a particular domain, field, or python library.
        - Acronyms of variables or concepts that appear in the codebase are also not acceptable.

            ```python
                # Bad
                hr = HordeRequest(...)

                # Good
                horde_request = HordeRequest(...)
            ```

            - This avoids ambiguity (consider if the above function also included a `HordeResponse`) and improves readability.

### Class Prefixes, Suffixes, and other Naming Conventions

Many classes contain standardized prefixes, suffixes, or identifiers within their names to indicate their purpose or behavior. These conventions help developers quickly understand the role of a class within the SDK.

#### General

- **Generic** (Always a Prefix): Refers to a class that is not specific to a particular API implementation. It serves as a base or abstract class that can be extended for different API clients or may be general-purpose.
    - Examples: `GenericHordeAPIManualClient`, `GenericAsyncHordeAPIManualClient`
- **Base** (Always a Prefix): Indicates a foundational class that provides core functionality and may be abstract or partially implemented. It is intended to be extended by more specific classes.
    - Examples: `BaseAIHordeClient`, `BaseAIHordeSimpleClient`

#### API/Client Specific

- **Manual**: Refers to classes that do not have context management or automatic session handling. These classes require the user to clean up server resources manually.
    - Examples: `AIHordeAPIManualClient`, `GenericHordeAPIManualClient`
- **Async**: Refers to classes that support asynchronous operations, allowing for non-blocking API calls and improved performance in concurrent environments. Generally, these classes will use `async` method definitions but may support synchronous operations as well.
    - Examples: `AIHordeAPIAsyncManualClient`, `GenericAsyncHordeAPIManualClient`
- **HordeAPI**: Indicates a class that is specifically designed for a Horde-style API. This *does not* imply that the class is specific to the AI Horde API, but rather that it is designed to work with any API that follows the Horde-style conventions.
    - Examples: `GenericHordeAPIManualClient`, `GenericAsyncHordeAPIManualClient`
- **AIHorde**: Refers to classes that are specifically designed for the AI Horde API. These classes are tailored to the specific requirements and features of the AI Horde API.
    - Examples: `AIHordeAPIManualClient`, `AIHordeAPIAsyncManualClient`
- **Session** (Always a suffix): Indicates a class that manages a session with the API, handling authentication, connection management, and request/response handling. These classes should provide context management support (i.e., they should implement the `__enter__` and `__exit__` or `__aenter__` and `__aexit__` methods) to ensure proper cleanup of resources.
    - Examples: `GenericHordeAPISession`, `GenericAsyncHordeAPISession`

#### Generation/Inference Specific

- **FeatureFlags**: Refers to classes which describe what features are required by a generation *or* what features are supported by a worker/backend.
    - Example: `ImageGenerationFeatureFlags`
- **GenerationParameters**/**Parameters**: Refers to classes which describe the parameters required for a generation request.
    - Example: `ImageGenerationParameters`
- **ParametersTemplate**: Refers to classes which describe the parameters required for a generation request, but have the property that **all fields are optional**. These classes are intended to be used as templates during the construction of certain other feature, such as user styles and chaining.
    - Example: `ImageGenerationParametersTemplate`
- **Basic**: Classes which have the parameters shared across all (or virtually all) generation requests of that kind. Images, for example, universally have a width and height, so `BasicImageGenerationParameters` would be a class that contains those fields.
    - Example: `BasicImageGenerationParameters`
- **KNOWN_**: `Enums` or `StrEnums` which describe a set of known values for a particular field or parameter. These are intended to be used as a way to validate input and provide a clear set of options for consumers. However, by convention, these are not *required* to be used, and consumers are free to use any valid value for the field or parameter as long as its type is correct.
    - Example: `KNOWN_IMAGE_SAMPLERS`, `KNOWN_AUX_MODEL_SOURCE`

## Error Handling

- Never silently handle exceptions. Always log and/or re-raise them.
- Exceptions should be used for exceptional and unhandled cases, not for control flow.
    - Exceptions should be raised for errors that are not expected to occur during normal operation of the program
- Bare `except:` statements are considered evil.
    - This is because they catch all exceptions, including system-exiting exceptions like `KeyboardInterrupt` and `SystemExit`, which can lead to unexpected behavior and make debugging difficult.
- Do not blanket catch exceptions (e.g., `except Exception as e:`) unless you have a very good reason to do so.
    - If you have a blanket catch, you should instead consider making the excepts opt-in (where the default is to `raise e`).
    - This does not apply where you are cleaning up resources or performing finalization tasks (e.g., closing files, releasing locks, etc.) where you may need to catch multiple exceptions (such as in a `__exit__` method).
    - If you must catch an exception, catch only the specific exception(s) that you expect to occur and can handle appropriately.

## Documentation

- All public modules, classes, methods, variables and fields must be documented with docstrings.
    - Docstrings should be written in [google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).
    - The first line of the docstring should be in the imperative mood and should be a brief summary of the method's purpose.
        - Avoid merely restating the method name unless the method is narrow or trivial in scope.
    - Methods marked with `@override` do not need a docstring because they inherit the docstring from the parent class. However, if the method's behavior is significantly different from the parent class, it should be documented with a docstring.
        - However, if this is the case, it should be considered a code smell and the method or parent method should be refactored to avoid the need for the overriding behavior to be so different.
    - Methods which perform validation of inputs (and therefore raise value or type errors) or have predictable failure modes should document these exceptions with a `Raises` section in the docstring.
        - For example, methods which are known to rely on external resources (e.g., network calls, file I/O) should document the exceptions that may be raised in the event of a failure.
        - It is **not** expected that every conceivable exception raised from a particular call hierarchy is documented, but rather those that are most likely to occur and can be reasonably anticipated.
            - A method that opens a file should document `FileNotFoundError` and `IOError` in its `Raises` section, while network-related methods should document `ConnectionError`, `TimeoutError`, and other relevant exceptions.
  
### API Model Specific Documentation

Many docstrings in the SDK have additional requirements when they are related to API models or requests/responses. While these rules would be difficult to remember, they are luckily enforced by CI and the `horde_sdk.meta` module has helper functions to assist in generating the required docstrings. The correct docstrings will also be emitted by the `object_verify` tests. Be sure to run the tests with `-s` to see the output.

- Children classes of `HordeAPIObject`, `HordeAPIData` which have a named model described in the API docs must have a docstring whose final line looks like this (for a model with the name `HordePerformance` on the v2 API):

    ```python
        """...

        v2 API Model: `HordePerformance`
        """
    ```

    Where `HordePerformance` is the name of the model as described in the API docs. It must be followed by a carriage return.

- Children classes of `HordeResponse` must have additional specific information, for example:

    When the response is returned from **one** endpoint:

    ```python
        class HordePerformanceResponse(HordeResponseBaseModel):
        """Information about the performance of the horde, such as worker counts and queue sizes.

        Represents the data returned from the /v2/status/performance endpoint with http status code 200.

        v2 API Model: `HordePerformance`
        """
    ```

    Where `/v2/status/performance` is the endpoint that returns the performance information. This must match the corresponding request class's `get_api_endpoint_subpath()` and `get_success_status_response_pairs()` values.

    When the response can be returned from **multiple** endpoints:

    ```python
    class ResponseModelCollection(HordeResponseBaseModel):
    """A collection of styles.

    Represents the data returned from the following endpoints and http status codes:
        - /v2/collection_by_name/{collection_name} | CollectionByNameRequest [GET] -> 200
        - /v2/collections/{collection_id} | CollectionByIDRequest [GET] -> 200

    v2 API Model: `ResponseModelCollection`
    """
    ```

    Where `/v2/collection_by_name/{collection_name}` and `/v2/collections/{collection_id}` are the endpoints that return the collection information. This must match the corresponding all of the requesting class's `get_api_endpoint_subpath()` and `get_success_status_response_pairs()` values.

- Children classes of `HordeRequest` must have additional specific information, for example:

    ```python
        class HordePerformanceRequest(BaseAIHordeRequest):
        """Request performance information about the horde, such as worker counts and queue sizes.

        Represents a GET request to the /v2/status/performance endpoint.
        """
    ```

- If the API does not name the model, `get_api_model_name(...)` must be overloaded to return `horde_sdk.consts._ANONYMOUS_MODEL` and the docstring should be:

    ```python
        """...

        v2 API Model: `_ANONYMOUS_MODEL`
        """
    ```

- If the model has is overloaded (has two or more conflicting representations), `get_api_model_name(...)` must be overloaded to return `horde_sdk.consts._OVERLOADED_MODEL` and the docstring should be:

    ```python
        """...

        v2 API Model: `_OVERLOADED_MODEL`
        """
    ```

## Function and Method Signatures

- Class and method signatures should prefer keyword-only arguments especially when there are multiple arguments of the same type and/or when they are adjacent to each other.
    - This improves readability and reduces the chance of passing arguments in the wrong order. Additionally, it improves the ability to add new arguments in the future without breaking existing code.
    - For example:

        ```python
            # Avoid this
            def create_user(name: str, age: int, username: str, email: str):
                ...

            create_user("John Doe", 30, "johndoe", "john.doe@example.com")


            # Do this instead
            def create_user(*, name: str, age: int, username: str, email: str):
                ...

            create_user(name="John Doe", age=30, username="johndoe", email="john.doe@example.com")
        ```

## Object-Oriented Design

- Many Object Oriented Principals (OOPs) are used, especially with class design, but python's dynamic nature should embraced when doing so would be pythonic (widely understood idiomatic python code).
    - Use inheritance when an object "is a" relationship exists.
    - Try to use composition over inheritance when an object "has a" relationship exists.
    - Use `@override` when overriding methods in a subclass.

## Method Overloading and Return Types

- Avoid surprisingly overloaded methods - methods with ambiguous or unexpected overloading.
    - For example, if a method is overloaded to accept either a single object or a list of objects, it should be clear from the method name and documentation that this is the case.
        - It would be best, however, that two separate methods are created instead.
- Methods should return a predictable type.
    - This is technically enforced by type hints, but it is still important to consider the implications of multiple types, especially from the perspective of a consumer.
    - Avoid returning `None` as a catch-all indication of failure. Either raise an exception or return a more specific value indicating the failure.
        - This is especially true if you are returning `None` for multiple *kinds* of failure, "not found" errors, or timeouts.
        - Of course, `None`/`null` has a widely understood meaning ('missing', 'unset') in most programming languages, and can be used whenever source data represents it this way or to indicate `None`'s usual meaning, just avoid overloading its meaning.
    - If possible, accept abstract types (e.g., `Iterable`, `Mapping`) instead of concrete types (e.g., `list`, `dict`) to allow for more flexibility in the return type.

        ```python
            # Avoid this
            def mutate_items(items: list[Item]) -> list[Item]:
                ...
            # Do this instead
            def mutate_items(items: Iterable[Item]) -> Iterable[Item]:
                ...
        ```

        - However, if appropriate, make the function generic so the type hinting is preserved.

            ```python
                from typing import TypeVar, Generic, Iterable

                T = TypeVar("T", bound=Iterable[Any])

                def mutate_items(items: T) -> T:
                    ...
            ```

        - This allows the consumer to use any iterable type (e.g., `list`, `set`, `tuple`) and still have the type hints preserved.
    - Type hint concrete types for return values to ensure that the consumer knows what to expect.
        - Unless
            - ... the method is specifically designed to return an abstract type
            - ... is an abstract superclass **and** a more specific type is not required
        - For example, if a method constructs and returns list, it should be type hinted as `list` and not `Iterable`.

            ```python
                # Avoid this
                def get_items(self) -> Iterable[Item]:
                    return [Item(), Item()]

                # Do this instead
                def get_items(self) -> list[Item]:
                    return [Item(), Item()]
            ```

    - The use of `Any` should be extremely judicious and should not be used when a more specific type can be used.
        - Careful consideration should be given to whether or not a consumer *might* care about the type of the return value.
        - In the SDK, a good example of good `Any` usage is type hinting `HordeSingleGeneration[Any]`, where the generic parameter represents the resulting types from the generation (e.g., `str` for text, `bytes` for images, etc.). This patterns allows accurately typing `HordeSingleGeneration` when working with arbitrary generations in contexts that the resulting type is not important, for example, in high-level generic worker classes.
        - With very few exceptions, `Any` should not be used as a return type hint *unless* it the object in question can have its type inferred by some other - obvious - means or in a more appropriate context.
    - Generally, for methods which mutate or return a different type based on input, it should be clear from the method name and documentation that this is the case and which types can be expected based on different inputs.
        - For example, the following method signature should be considered bad practice:

          ```python
            # Bad
            def get_items(self, as_list: bool = True) -> list[Item] | set[Item]:
                ...

            # Good
            def get_items(self) -> list[Item]:
                ...
            def get_unique_items(self) -> set[Item]:
                ...
          ```

    - Methods which *can* return a list or a container should *always* return a list or container, even if it is a single item.
        - For example, the following method signature should be considered bad practice:

          ```python
            # Bad
            def get_items(self) -> list[Item] | Item:
                ...

            # Good
            def get_items(self) -> list[Item]:
                ...
          ```

    - Methods should avoid returning different container types *unless that is the purpose of the method*.
        - For example, the following method signatures should be considered bad practice:

          ```python
            # Bad
            def get_items(self) -> list[Item] | set[Item]:
                ...

            # Bad
            def get_items(self, as_dict: bool = False) -> list[Item] | dict[Item]:
                ...

            # Good
            def get_items(self) -> list[Item]:
                ...
            def get_items_mapping(self) -> dict[Item]:
                ...
          ```

    - Instead, consider using a single container type and providing a separate method to convert to another type if needed.
    - However, this should not be considered a ban on returning different container types if the method is specifically designed to do so or if it is clear from the method name and documentation that this is the case.

## Control Flow and Readability

- Prefer guard clauses over deeply nested if statements.
    - For example:

        ```python
        # Avoid this
        def process_item(item: Item):
            if item is not None:
                if item.is_valid():
                    # process item
                    ...
        # Do this instead
        def process_item(item: Item):
            if item is None or not item.is_valid():
                return
            # process item
            ...

        ```

- Prefer meaningfully named composite `bool` conditionals over complex multi-line `if` statements.
    - For example:

        ```python
        # Avoid this
        def is_valid_item(item: Item) -> bool:
            if (item.has_name() and item.has_value()) or
                (item.has_description() and item.description_valid()):
                if item.is_active():
                    return True
            return False

        # Do this instead
        def is_valid_item(item: Item) -> bool:
            has_name_and_value = item.has_name() and item.has_value()
            has_description_and_valid = item.has_description() and item.description_valid()

            return (has_name_and_value or has_description_and_valid) and item.is_active()
        ```

## Data Structures, Models, and Constants

- Classes should be preferred over dictionaries or other anonymous data structures (e.g., raw 3 tuples).
    - Classes should be used to represent complex data structures or objects, especially when they have behavior associated with them.
    - `BaseModel` derived classes from [pydantic](https://docs.pydantic.dev/) should be used to represent data structures or objects when possible.
        - This provides validation and conversion of data types, which is especially important when dealing with data from external sources such as APIs.
        - However, when robust validation is not needed, or when performance is a (verifiable) concern, simple classes can be used instead.
- Use properties to provide read-only access to class attributes when appropriate.
    - This implies you should avoid returning or exposing mutable members of a class, instead preferring to return a copy.
        - For example, instead of:

      ```python
      class Item:
          def __init__(self, data: dict):
              self.data = data

          def get_data(self) -> dict:
              return self.data
      ```

      Prefer:

      ```python
      class Item:
          def __init__(self, data: dict):
              self._data = data

          def get_data(self) -> dict:
              return self._data.copy()
      ```

- Magic strings or magic numbers should be considered evil.
    - Magic strings or numbers are values that are hard-coded into the code and have no clear meaning.
    - `StrEnum`s should be used to represent strings with a specific set of valid values and regular constants can be used for isolated (unconnected) values.
    - `Enum`s should be used to represent numbers with a specific set of valid values and regular constants can be used for isolated (unconnected) values.
    - If many constants relate to each other, they should be grouped into a class.

        ```python
            # Avoid this
            MAX_RETRIES = 5
            TIMEOUT = 30
            JITTER = 0.1
            ...

            # Good
            class APIConfig:
                MAX_RETRIES = 5
                TIMEOUT = 30
                JITTER = 0.1
                ...
        ```

### "KNOWN" Constants

- For consumer convenience, parameters which have a fixed set of known values should be defined as constants in an appropriate `consts.py` file. These constants should be named with the `KNOWN_` prefix and should be defined as `StrEnum`s or `Enum`s as appropriate.
- However, these values should **always be considered optional**. Consumers of the SDK should be able to use any valid value for the parameter as long as its type is correct. It would be ideal, but not required, that classes or functions which require these parameters validate them against the live API at runtime.
    - ***Rationale***: This prevents the SDK from needing to be updated every time a new value is added to an API, and allows consumers to use any valid value without needing to wait for an SDK update.

## Imports and Module Export

- Star imports are considered evil.
- Significant namespaces must explicitly export all public members via `__all__`
    - This includes classes, functions, and variables that are intended to be used by consumers of the module.

## Pydantic BaseModel Usage

- `BaseModel` derived classes should be used in a DataClass-like manner.
    - They should not implement any methods or properties which require any side effects or have any state.
    - ***Rationale***: [pydantic](https://docs.pydantic.dev)'s `BaseModel` provides robust validation and conversion of data types. Mutating the state of a model bypasses this validation and conversion.
        - However, methods which perform validation or conversion of the data are allowed, but should be narrow in scope.
            - **Exception**: Values should never be coerced to `None` for optional fields when passed a non-`None` value.
                - ***Rationale***: If an invalid value is passed to a field, it should be raised as an error. This is especially important when implementing a "Template" class (which all fields are optional) - if a child class overrides a field to be non-optional but the parent class is coercing it to `None`, this can cause bugs or run-time errors.
        - As a general rule, if a function in a `BaseModel` derived class extends beyond `isinstance` or value checking, it probably should be moved to a different class or utility function.
    - `BaseModel` derived classes used as API responses or members of an API response should be frozen. Additionally, classes meant to represent data set by a client, server, or worker should also be frozen.
        - **Important**: This is not a blanket requirement for all `BaseModel` derived classes. Consider carefully how likely it would that a consumer would want to modify the data in the model and if doing so would have unintended consequences difficult for consumers to understand.
        - ***Rationale***: Classes of this kind being frozen reflects the fact that they are not meant to be modified after creation. Workers receiving jobs from the server (and specified by the client) should never need to modify that job data. Raising errors in the case a worker attempts to modify job data prevents accidental modification and prevents a category of bugs.
        - This is done by setting the field `model_config` to an instance of a `ConfigDict`.
            - See `get_default_frozen_model_config_dict()` in the top-level namespace (`horde_sdk.__init__.py`) for the default frozen model config.
                - This function should be used whenever possible to set the `model_config` field.
                - Using this function ensures that the model config is consistent across the codebase.
                - Further, the CI/Testing relies on using this function to ensure that the models are frozen in tests.
                - If you set your own `model_config`, you must ensure that it is consistent with the behavior of `get_default_frozen_model_config_dict()`.

## API Model Verification

These rules are specific to (remote) API models (for example, any class in an `apimodels` namespace).

1. **All `HordeAPIObject` and `HordeAPIData` sub-classes must be imported** in their appropriate apimodels `__init__.py` files so that they match the live API surface.
    - For example, all AI Horde API models must be imported into `horde_sdk.ai_horde_api/apimodels/__init__.py`.
    - ***Rationale***: This ensures that the SDK's API surface matches the live API surface and that all models are properly documented and tested. The testing relies on these imports to function correctly. Further, this ensures that all models are appropriately exposed for consumers of the SDK.
2. **Any model in the API docs** must be defined in the SDK. Unreferenced or missing models will cause a test failure.
3. **All endpoints in the API docs** must be handled or marked as ignored (e.g., admin-only or deprecated). Unknown or unaddressed endpoints raise errors during testing.
4. **All models must have docstrings** conforming to the style documented above. If they do not, these tests will fail and suggest required changes.
5. **All models (including requests and responses) must be instantiable from example JSON** found in the test data directories. If instantiation fails, the test will provide details on what's wrong.
6. **All request/response types must be hashable** if they aren't explicitly marked as unhashable (`@Unhashable`), which ensures they can be properly used in collections.
7. **All request/response types must be equatable** if they aren't explicitly marked as unequatable (`@Unequatable`), which ensures they can be properly compared in tests.
8. **Example payloads, response data, and production responses** must be valid according to their corresponding model validation rules, ensuring that the models accurately represent real-world data.
