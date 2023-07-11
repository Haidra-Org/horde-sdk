# horde_sdk

With the power of pydantic, you can simplify interfacing with the [AI-Horde's suite of APIs](https://github.com/db0/AI-Horde). Whether you want to request your own images, or roll your own worker software, this package may suit your needs for anything horde related.

## General notes
- Certain API models have attributes which may collide with a python builtin, such as `id` or `type`. In these cases, the attribute has a trailing underscore, as in `id_`. Ingested json still will work with the field 'id' (its a alias).

## AI-Horde
`TODO`

## Ratings API
There is currently some support for the [Image Ratings](https://dbzer0.com/blog/the-image-ratings-are-flooding-in/) API that are rating images from the [DiffusionDB](https://poloclub.github.io/diffusiondb/) dataset. See `example.py` for an idea of how to start.
