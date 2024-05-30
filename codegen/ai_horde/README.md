# Codegen helpers

This may help with some of the boiler plate code, and may save some typing when constructing new API model support.

Please note that this isn't a silver bullet, and the classes won't work (at all) as is. You should familiarize yourself with a non-trivial preexisting API model in the horde_sdk codebase, if you haven't already, if you intend to add additional models using this procedure as a base.

Install [api-spec-converter](https://github.com/LucyBot-Inc/api-spec-converter)
```bash
# (in node initialized console)
npm install -g api-spec-converter
```

Install [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)

```bash
# (in node initialized console)
pip install datamodel-code-generator
```

Convert the spec from [swagger](https://swagger.io/specification/v2/) to [OpenAPI 3](https://swagger.io/specification/):

```bash
api-spec-converter --from=swagger_2 --to=openapi_3 swagger.json > swagger_openapi3.json
```

Generate the code:
```bash
datamodel-codegen --input swagger_openapi3.json --output ai_horde_codegen.py --output-model-type pydantic_v2.BaseModel --use-union-operator --field-constraints
```

Standardize quotes with black:
```bash
black ai_horde_codegen.py
```

Clean up issues with datamodel-code-generator v0.21.1
```bash
python codegen_regex_fixes.py ai_horde_codegen.py
```

Format again, this time truncating the lines with `--preview`, and auto-fix lint problems
```bash
black ai_horde_codegen.py --unstable --enable-unstable-feature string_processing
ruff ai_horde_codegen.py --fix
black ai_horde_codegen.py --unstable --enable-unstable-feature string_processing # for good measure
ruff ai_horde_codegen.py --fix # for good measure
```

* Fix Enum classes
  * Defaults will be literals instead of enum members
  * There are duplicate classes
