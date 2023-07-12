# Getting Started

See `installation` for installation instructions.

## General Notes and Guidance

### Typing

-   Under the hood, **this project is strongly typed**. Practically,
    this shouldn't leak out too much and should mostly be contained to
    validation logic.
    -   If you do find something won't work because of type issues, but
        you think it should, please [file an issue on
        github](https://github.com/Haidra-Org/horde-sdk/issues).
-   This project relies very heavily on [pydantic
    2.0](https://docs.pydantic.dev/2.0/). If you are unfamiliar with the
    concepts of pydantic, you may be served by glancing at the
    documentation for it before consuming this library.
    -   Every class from this library potentially has validation on its
        `__init__(...)` function. You should be prepared to handle
        pydantic's <span class="title-ref">ValidationError</span>
        exception as a result.
    -   Most classes from this library have a `model_dump(...)` ([see
        the
        doc](https://docs.pydantic.dev/2.0/usage/serialization/#modelmodel_dump))
        method which will return a dictionary representation of the
        object if you would rather deal with that than the object
        itself.
    -   If you have json or a compatible dict, you can use
        [model_validate](https://docs.pydantic.dev/2.0/api/main/#pydantic.main.BaseModel.model_validate)
        or
        [model_validate_json](https://docs.pydantic.dev/2.0/api/main/#pydantic.main.BaseModel.model_validate_json)

### Inheritance

-   At first glance, the hierarchy of classes may seem a bit confusing.
    Rest assured, however, that these very docs are very helpful here.
    All relevant inherited attributes and functions are included in the
    child class documentation. Accordingly if you are looking at the
    code, and don't want to go up the hierarchy and figure out the
    inheritance, use these docs to see the resolved attributes and
    functions.

### Naming

-   Objects serializable to an API request are suffixed with `Request`.
-   Objects serializable to an API response are suffixed with
    `Response`.
-   Objects which are not meant to be instantiated are prefixed with
    `Base`.
    -   These in-between objects are typically logically-speaking parent
        classes of multiple API objects, but do not represent an actual
        API object on their own.
    -   See `horde_sdk.generic_api.apimodels` for some of the key
        `Base*` classes.
-   Certain API models have attributes which would collide with a python
    builtin, such as `id` or `type`. In these cases, the attribute has a
    trailing underscore, as in `id_`. Ingested json still will work with
    the field <span class="title-ref">id</span>\` (its a alias).

### Faux Immutability (or 'Why can't I change this attribute?!')

-   All of the \*Request and \*Response class, and many other classes,
    implement faux immutability, and their attributes are **read only**.
-   This is to prevent you from side stepping any validation.
-   See [pydantic's
    docs](https://docs.pydantic.dev/2.0/usage/validation_errors/#frozen_instance)
    for more information. See a
-   See also `faq` for more information.

# Examples

<div class="note" markdown="1">

<div class="title" markdown="1">

Note

</div>

TODO: Add examples

</div>
