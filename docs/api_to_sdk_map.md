# AI-Horde API Model to SDK Class Map
This is a mapping of the AI-Horde API models (defined at [https://stablehorde.net/api/](https://stablehorde.net/api/), see also [the swagger doc](https://stablehorde.net/api/swagger.json)) to the SDK classes.

## Payloads
| API Endpoint | HTTP Method | SDK Request Type |
| ------------ | ----------- | ---------------- |
| /v2/documents/privacy | GET | [AIHordeGetPrivacyPolicyRequest][horde_sdk.ai_horde_api.apimodels._documents.AIHordeGetPrivacyPolicyRequest] |
| /v2/documents/sponsors | GET | [AIHordeGetSponsorsRequest][horde_sdk.ai_horde_api.apimodels._documents.AIHordeGetSponsorsRequest] |
| /v2/documents/terms | GET | [AIHordeGetTermsRequest][horde_sdk.ai_horde_api.apimodels._documents.AIHordeGetTermsRequest] |
| /v2/find_user | GET | [FindUserRequest][horde_sdk.ai_horde_api.apimodels._find_user.FindUserRequest] |
| /v2/generate/async | POST | [ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncRequest] |
| /v2/generate/check/{id} | GET | [ImageGenerateCheckRequest][horde_sdk.ai_horde_api.apimodels.generate._check.ImageGenerateCheckRequest] |
| /v2/generate/pop | POST | [ImageGenerateJobPopRequest][horde_sdk.ai_horde_api.apimodels.generate._pop.ImageGenerateJobPopRequest] |
| /v2/generate/status/{id} | DELETE | [DeleteImageGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate._status.DeleteImageGenerateRequest] |
| /v2/generate/status/{id} | GET | [ImageGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate._status.ImageGenerateStatusRequest] |
| /v2/generate/submit | POST | [ImageGenerationJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.generate._submit.ImageGenerationJobSubmitRequest] |
| /v2/generate/text/async | POST | [TextGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.text._async.TextGenerateAsyncRequest] |
| /v2/generate/text/pop | POST | [TextGenerateJobPopRequest][horde_sdk.ai_horde_api.apimodels.generate.text._pop.TextGenerateJobPopRequest] |
| /v2/generate/text/status/{id} | DELETE | [DeleteTextGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate.text._status.DeleteTextGenerateRequest] |
| /v2/generate/text/status/{id} | GET | [TextGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate.text._status.TextGenerateStatusRequest] |
| /v2/generate/text/submit | POST | [TextGenerationJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.generate.text._submit.TextGenerationJobSubmitRequest] |
| /v2/interrogate/async | POST | [AlchemyAsyncRequest][horde_sdk.ai_horde_api.apimodels.alchemy._async.AlchemyAsyncRequest] |
| /v2/interrogate/pop | POST | [AlchemyPopRequest][horde_sdk.ai_horde_api.apimodels.alchemy._pop.AlchemyPopRequest] |
| /v2/interrogate/status/{id} | DELETE | [AlchemyDeleteRequest][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyDeleteRequest] |
| /v2/interrogate/status/{id} | GET | [AlchemyStatusRequest][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyStatusRequest] |
| /v2/interrogate/submit | POST | [AlchemyJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.alchemy._submit.AlchemyJobSubmitRequest] |
| /v2/kudos/transfer | POST | [KudosTransferRequest][horde_sdk.ai_horde_api.apimodels._kudos.KudosTransferRequest] |
| /v2/stats/img/models | GET | [ImageStatsModelsRequest][horde_sdk.ai_horde_api.apimodels._stats.ImageStatsModelsRequest] |
| /v2/stats/img/totals | GET | [ImageStatsModelsTotalRequest][horde_sdk.ai_horde_api.apimodels._stats.ImageStatsModelsTotalRequest] |
| /v2/stats/text/models | GET | [TextStatsModelsRequest][horde_sdk.ai_horde_api.apimodels._stats.TextStatsModelsRequest] |
| /v2/stats/text/totals | GET | [TextStatsModelsTotalRequest][horde_sdk.ai_horde_api.apimodels._stats.TextStatsModelsTotalRequest] |
| /v2/status/heartbeat | GET | [AIHordeHeartbeatRequest][horde_sdk.ai_horde_api.apimodels._status.AIHordeHeartbeatRequest] |
| /v2/status/models | GET | [HordeStatusModelsAllRequest][horde_sdk.ai_horde_api.apimodels._status.HordeStatusModelsAllRequest] |
| /v2/status/models/{model_name} | GET | [HordeStatusModelsSingleRequest][horde_sdk.ai_horde_api.apimodels._status.HordeStatusModelsSingleRequest] |
| /v2/status/news | GET | [NewsRequest][horde_sdk.ai_horde_api.apimodels._status.NewsRequest] |
| /v2/status/performance | GET | [HordePerformanceRequest][horde_sdk.ai_horde_api.apimodels._status.HordePerformanceRequest] |
| /v2/users | GET | [ListUsersDetailsRequest][horde_sdk.ai_horde_api.apimodels._users.ListUsersDetailsRequest] |
| /v2/users/{user_id} | PUT | [ModifyUserRequest][horde_sdk.ai_horde_api.apimodels._users.ModifyUserRequest] |
| /v2/users/{user_id} | GET | [SingleUserDetailsRequest][horde_sdk.ai_horde_api.apimodels._users.SingleUserDetailsRequest] |
| /v2/workers | GET | [AllWorkersDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers._workers.AllWorkersDetailsRequest] |
| /v2/workers/name/{worker_name} | GET | [SingleWorkerNameDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers._workers.SingleWorkerNameDetailsRequest] |
| /v2/workers/{worker_id} | DELETE | [DeleteWorkerRequest][horde_sdk.ai_horde_api.apimodels.workers._workers.DeleteWorkerRequest] |
| /v2/workers/{worker_id} | PUT | [ModifyWorkerRequest][horde_sdk.ai_horde_api.apimodels.workers._workers.ModifyWorkerRequest] |
| /v2/workers/{worker_id} | GET | [SingleWorkerDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers._workers.SingleWorkerDetailsRequest] |


## Responses
| API Endpoint | HTTP Status Code | SDK Response Type |
| ------------ | ----------- | ----------------- |
| /v2/documents/privacy | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels._documents.HordeDocument] |
| /v2/documents/sponsors | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels._documents.HordeDocument] |
| /v2/documents/terms | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels._documents.HordeDocument] |
| /v2/find_user | 200 | [UserDetailsResponse][horde_sdk.ai_horde_api.apimodels._users.UserDetailsResponse] |
| /v2/generate/async | 200 | [ImageGenerateAsyncDryRunResponse][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncDryRunResponse] |
| /v2/generate/async | 202 | [ImageGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate._async.ImageGenerateAsyncResponse] |
| /v2/generate/check/{id} | 200 | [ImageGenerateCheckResponse][horde_sdk.ai_horde_api.apimodels.generate._check.ImageGenerateCheckResponse] |
| /v2/generate/pop | 200 | [ImageGenerateJobPopResponse][horde_sdk.ai_horde_api.apimodels.generate._pop.ImageGenerateJobPopResponse] |
| /v2/generate/status/{id} | 200 | [ImageGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate._status.ImageGenerateStatusResponse] |
| /v2/generate/submit | 200 | [JobSubmitResponse][horde_sdk.ai_horde_api.apimodels.base.JobSubmitResponse] |
| /v2/generate/text/async | 200 | [TextGenerateAsyncDryRunResponse][horde_sdk.ai_horde_api.apimodels.generate.text._async.TextGenerateAsyncDryRunResponse] |
| /v2/generate/text/async | 202 | [TextGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate.text._async.TextGenerateAsyncResponse] |
| /v2/generate/text/pop | 200 | [TextGenerateJobPopResponse][horde_sdk.ai_horde_api.apimodels.generate.text._pop.TextGenerateJobPopResponse] |
| /v2/generate/text/status/{id} | 200 | [TextGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate.text._status.TextGenerateStatusResponse] |
| /v2/generate/text/submit | 200 | [JobSubmitResponse][horde_sdk.ai_horde_api.apimodels.base.JobSubmitResponse] |
| /v2/interrogate/async | 202 | [AlchemyAsyncResponse][horde_sdk.ai_horde_api.apimodels.alchemy._async.AlchemyAsyncResponse] |
| /v2/interrogate/pop | 200 | [AlchemyPopResponse][horde_sdk.ai_horde_api.apimodels.alchemy._pop.AlchemyPopResponse] |
| /v2/interrogate/status/{id} | 200 | [AlchemyStatusResponse][horde_sdk.ai_horde_api.apimodels.alchemy._status.AlchemyStatusResponse] |
| /v2/interrogate/submit | 200 | [AlchemyJobSubmitResponse][horde_sdk.ai_horde_api.apimodels.alchemy._submit.AlchemyJobSubmitResponse] |
| /v2/kudos/transfer | 200 | [KudosTransferResponse][horde_sdk.ai_horde_api.apimodels._kudos.KudosTransferResponse] |
| /v2/stats/img/models | 200 | [ImageStatsModelsResponse][horde_sdk.ai_horde_api.apimodels._stats.ImageStatsModelsResponse] |
| /v2/stats/img/totals | 200 | [ImageStatsModelsTotalResponse][horde_sdk.ai_horde_api.apimodels._stats.ImageStatsModelsTotalResponse] |
| /v2/stats/text/models | 200 | [TextStatsModelResponse][horde_sdk.ai_horde_api.apimodels._stats.TextStatsModelResponse] |
| /v2/stats/text/totals | 200 | [TextStatsModelsTotalResponse][horde_sdk.ai_horde_api.apimodels._stats.TextStatsModelsTotalResponse] |
| /v2/status/heartbeat | 200 | [AIHordeHeartbeatResponse][horde_sdk.ai_horde_api.apimodels._status.AIHordeHeartbeatResponse] |
| /v2/status/models | 200 | [HordeStatusModelsAllResponse][horde_sdk.ai_horde_api.apimodels._status.HordeStatusModelsAllResponse] |
| /v2/status/models/{model_name} | 200 | [HordeStatusModelsSingleResponse][horde_sdk.ai_horde_api.apimodels._status.HordeStatusModelsSingleResponse] |
| /v2/status/news | 200 | [NewsResponse][horde_sdk.ai_horde_api.apimodels._status.NewsResponse] |
| /v2/status/performance | 200 | [HordePerformanceResponse][horde_sdk.ai_horde_api.apimodels._status.HordePerformanceResponse] |
| /v2/users | 200 | [ListUsersDetailsResponse][horde_sdk.ai_horde_api.apimodels._users.ListUsersDetailsResponse] |
| /v2/users/{user_id} | 200 | [UserDetailsResponse][horde_sdk.ai_horde_api.apimodels._users.UserDetailsResponse] |
| /v2/workers | 200 | [AllWorkersDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers._workers.AllWorkersDetailsResponse] |
| /v2/workers/name/{worker_name} | 200 | [SingleWorkerDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers._workers.SingleWorkerDetailsResponse] |
| /v2/workers/{worker_id} | 200 | [SingleWorkerDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers._workers.SingleWorkerDetailsResponse] |
