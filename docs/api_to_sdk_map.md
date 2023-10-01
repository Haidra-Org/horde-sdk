# AI-Horde API Model to SDK Class Map
This is a mapping of the AI-Horde API models (defined at [https://stablehorde.net/api/](https://stablehorde.net/api/), see also [the swagger doc](https://stablehorde.net/api/swagger.json)) to the SDK classes.

## Payloads
| API Endpoint | HTTP Method | SDK Request Type |
| ------------ | ----------- | ---------------- |
| /v2/find_user | GET | [FindUserRequest][horde_sdk.ai_horde_api.apimodels._find_user.FindUserRequest] |
| /v2/generate/async | POST | [ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncRequest] |
| /v2/generate/check/{id} | GET | [ImageGenerateCheckRequest][horde_sdk.ai_horde_api.apimodels.generate._check.ImageGenerateCheckRequest] |
| /v2/generate/pop | POST | [ImageGenerateJobPopRequest][horde_sdk.ai_horde_api.apimodels.generate._pop.ImageGenerateJobPopRequest] |
| /v2/generate/status/{id} | DELETE | [DeleteImageGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate._status.DeleteImageGenerateRequest] |
| /v2/generate/status/{id} | GET | [ImageGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate._status.ImageGenerateStatusRequest] |
| /v2/generate/submit | POST | [ImageGenerationJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.generate._submit.ImageGenerationJobSubmitRequest] |
| /v2/interrogate/async | POST | [AlchemyAsyncRequest][horde_sdk.ai_horde_api.apimodels.alchemy._async.AlchemyAsyncRequest] |
| /v2/interrogate/pop | POST | [AlchemyPopRequest][horde_sdk.ai_horde_api.apimodels.alchemy._pop.AlchemyPopRequest] |
| /v2/interrogate/status/{id} | DELETE | [AlchemyDeleteRequest][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyDeleteRequest] |
| /v2/interrogate/status/{id} | GET | [AlchemyStatusRequest][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyStatusRequest] |
| /v2/stats/img/models | GET | [StatsImageModelsRequest][horde_sdk.ai_horde_api.apimodels._stats.StatsImageModelsRequest] |
| /v2/workers | GET | [AllWorkersDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers._workers_all.AllWorkersDetailsRequest] |


## Responses
| API Endpoint | HTTP Status Code | SDK Response Type |
| ------------ | ----------- | ----------------- |
| /v2/find_user | 200 | [FindUserResponse][horde_sdk.ai_horde_api.apimodels._find_user.FindUserResponse] |
| /v2/generate/async | 200 | [ImageGenerateAsyncDryRunResponse][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncDryRunResponse] |
| /v2/generate/async | 202 | [ImageGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse] |
| /v2/generate/check/{id} | 200 | [ImageGenerateCheckResponse][horde_sdk.ai_horde_api.apimodels.generate._check.ImageGenerateCheckResponse] |
| /v2/generate/pop | 200 | [ImageGenerateJobPopResponse][horde_sdk.ai_horde_api.apimodels.generate._pop.ImageGenerateJobPopResponse] |
| /v2/generate/status/{id} | 200 | [ImageGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate._status.ImageGenerateStatusResponse] |
| /v2/generate/submit | 200 | [JobSubmitResponse][horde_sdk.ai_horde_api.apimodels.base.JobSubmitResponse] |
| /v2/interrogate/async | 202 | [AlchemyAsyncResponse][horde_sdk.ai_horde_api.apimodels.alchemy._async.AlchemyAsyncResponse] |
| /v2/interrogate/pop | 200 | [AlchemyPopResponse][horde_sdk.ai_horde_api.apimodels.alchemy._pop.AlchemyPopResponse] |
| /v2/interrogate/status/{id} | 200 | [AlchemyStatusResponse][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyStatusResponse] |
| /v2/stats/img/models | 200 | [StatsModelsResponse][horde_sdk.ai_horde_api.apimodels._stats.StatsModelsResponse] |
| /v2/workers | 200 | [AllWorkersDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers._workers_all.AllWorkersDetailsResponse] |
