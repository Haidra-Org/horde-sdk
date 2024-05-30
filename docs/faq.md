title: Frequently Asked Questions

# Why can't I change an attribute of one of my \*Response or \*Request objects?

> The objects returned by horde_sdk are immutable. If you need to change
> something, you'll need to create a new object with the changes you
> want. See the [section in getting started](getting_started.md#faux-immutability) for more info.

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
> pydantic's `.model_dump()` ('to dict') `.model_validate()` ('from dict').

# The apimodels have a lot of getters and I don't think they're very pythonic; Why don't use you use more properties?

> The implementation of the property decorator is not [very friendly to non-instance methods](https://bugs.python.org/issue45356), and is in fact deprecated for that use in 3.11.
>
> The API model hierarchy relies on (at least logically speaking) class-level
> information to facilitate maintainability and extensibility. Any method
> marked as a `@classmethod` contains information that should not necessarily
> require an instance to access, as they are shared across all instances,
> and consumers of the library may find themselves in situations where
> accessing this information prior to instantiation may be warranted, or even
> very useful.
>
> Ultimately, aside from the `get_` prefix, the only other practical or
> functional difference is the need to use `()` to invoke it as a function.
