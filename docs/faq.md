title: Frequently Asked Questions

# Why can't I change an attribute of one of my \*Response or \*Request objects?

> The objects returned by horde_sdk are immutable. If you need to change
> something, you'll need to create a new object with the changes you
> want. See the [section in getting started](../getting_started/#faux-immutability-or-why-cant-i-change-this-attribute) for more info.

# I don't like types. Why is this library so focused on them?

> Types are a great way to ensure that your code is correct. They also
> make it easier for other developers to understand what your code is
> doing with [type
> hints](https://docs.python.org/3/library/typing.html). These *hint*
> what data format variables or functions are expecting or will
> return. This is how IDEs such as PyCharm or VSCode can provide
> autocomplete and other helpful features.
>
> If you don't like working with the objects from this library within
> your own code, you can always translate between the types and dicts using
> pydantic's `.model_dump()` `.model_validate()`. There is also a convenience
> function [to_json_horde_sdk_safe()](../horde_sdk/generic_api/apimodels/#horde_sdk.generic_api.apimodels.HordeAPIModel.to_json_horde_sdk_safe)
> which may be useful. All API models in this library have this method,
> but certain other classes may not.
