# Package Structure

## API Support Packages

API support packages do the following:

- Implement one or more client types from `horde_sdk.generic_api.generic_clients`.
  - This requires extending, as needed, the following classes from `horde_sdk.generic_api.metadata`:
    - `GenericHeaderFields`
    - `GenericAcceptTypes`
    - `GenericPathFields`
    - `GenericQueryFields`
    - Adding values to these fields implies that python objects with fields of the same name are *always* passed to the API this way.
      - e.g., adding a field named `api_key` to `GenericHeaderFields` implies that any request using that client with a field named `api_key` in its definition will always be passed as a header field named `api_key`.
  - These are passed to client class constructors so the underlying shared client logic can handle the specific fields and headers for the API.
  - `GENERIC_API_ENDPOINT_SUBPATH` from `horde_sdk.generic_api.endpoints` is used to determine url paths for the API. It must be extended to include all addressable endpoints for that API. See `horde_sdk.ai_horde_api.endpoints` for an example.
- API models for requests (including payloads and parameters) and responses
- Constants for API endpoints and other configurations
  - Some examples include the valid values for parameters which accept only certain strings.
  - This also includes consts for default timeout values, default anonymous API keys, etc.
  
```bash
ai_horde_api/
├── apimodels/
├──── __init__.py
├──── ... (other API model files)
├── __init__.py
├── ai_horde_clients.py
├── consts.py
├── exceptions.py
├── endpoints.py
├── metadata.py
├── utils.py
├── ... (other files)
```

By convention, the following files within an api support package should always contain certain types of content:

- `__init__.py` (at the root of the api support package)
  - Must import **all** client classes, exceptions and members of the endpoint module.
  - If there are few API models and that is reasonably expected to always be the case, they may also be imported here.
- `apimodels/` or `apimodels.py`
  - Contains API models for requests and responses, as well as any other data structures used in that API's interactions.
  - Contrast this with the classes found in the `horde_sdk.generation_parameters` module which contain data structures that may be used outside the context of a specific API (such as locally using a backend).
  - `apimodels/__init__.py` or `apimodels.py`
    - Must import **all** API models from the `apimodels/` and must be included in the `__all__` module variable.
- `*_clients.py` or `clients/`
  - Contains client classes that implement the API interactions using the models defined in `apimodels/`.
  - Must import **all** client classes from the `clients/` and must be included in the `__all__` module variable.
- `consts.py`
  - Contains constants related to the API, such as endpoint URLs, default values, and other configuration settings.
  - Must import **all** constants from the `consts.py` and must be included in the `__all__` module variable.
- `exceptions.py`
  - Contains custom exceptions related to the API interactions.
  - Must import **all** exceptions from the `exceptions.py` and must be included in the `__all__` module variable.
- `endpoints.py`
  - Contains the endpoint subpaths for the API, which are used to construct full URLs for API requests.
- `metadata.py`
  - Contains metadata classes that define the header fields, query parameters, and other metadata used in API requests.
- `utils.py`
  - Contains utility functions related to the API interactions, such as helper functions for constructing requests or processing responses.
  - Consider adding a `utils/` directory if there are numerous utility functions.
  - Also consider adding generic (non-api-specific) utility functions to `horde_sdk.generic_api.utils` if they are applicable to multiple APIs or `horde_sdk.utils` if they have broad applicability.

## Generation Parameters

- `generation_parameters/__init__.py`
  - Must import **all** generation parameter classes as well as related constants/enums and must be included in the `__all__` module variable.
- `generation_parameters/{generation_type}/__init__.py`
  - Must import **all** generation parameter classes for that specific generation type as well as related constants/enums and must be included in the `__all__` module variable.
- `generation_parameters/{generation_type}/object_models.py` or `generation_parameters/{generation_type}/object_models/*`
  - Contains data structures representing parameters for generation that are not specific to any one API.
  - All top level classes (and classes which they contain) should always inherit from an appropriate base class in `horde_sdk.generation_parameters.generic.object_models`.
- `generation_parameters/{generation_type}/consts.py`
  - Contains constants related to the generation parameters for that specific generation type, such as default values, valid options, and other configuration settings.
  - Consider if these constants are applicable to multiple generation types and if so, place them in `horde_sdk.generation_parameters.generic.consts.py` instead.
