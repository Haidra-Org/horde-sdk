---
title: "AI Horde endpoint map"
summary: "Map each AI Horde endpoint and HTTP method to its SDK request and successful response types."
topics: [api-models, requests]
order: 90
---

# AI Horde endpoint map

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [api-models](../topics.md#api-models), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

This table is derived directly from concrete `HordeRequest` metadata. Endpoint, HTTP method, and success status together
identify a row; this preserves operations that share a path or status.

<!-- BEGIN GENERATED: endpoint-map (build_docs.py) -->
| Endpoint | Method | Request type | Success | Response type |
| --- | --- | --- | ---: | --- |
| `/v2/collection_by_name/{collection_name}` | `GET` | [CollectionByNameRequest][horde_sdk.ai_horde_api.apimodels.collections.CollectionByNameRequest] | 200 | [ResponseModelCollection][horde_sdk.ai_horde_api.apimodels.collections.ResponseModelCollection] |
| `/v2/collections` | `GET` | [AllCollectionsRequest][horde_sdk.ai_horde_api.apimodels.collections.AllCollectionsRequest] | 200 | [AllCollectionsResponse][horde_sdk.ai_horde_api.apimodels.collections.AllCollectionsResponse] |
| `/v2/collections` | `POST` | [CreateCollectionRequest][horde_sdk.ai_horde_api.apimodels.collections.CreateCollectionRequest] | 200 | [CreateCollectionResponse][horde_sdk.ai_horde_api.apimodels.collections.CreateCollectionResponse] |
| `/v2/collections/{collection_id}` | `DELETE` | [DeleteCollectionRequest][horde_sdk.ai_horde_api.apimodels.collections.DeleteCollectionRequest] | 200 | [DeleteCollectionResponse][horde_sdk.ai_horde_api.apimodels.collections.DeleteCollectionResponse] |
| `/v2/collections/{collection_id}` | `GET` | [CollectionByIDRequest][horde_sdk.ai_horde_api.apimodels.collections.CollectionByIDRequest] | 200 | [ResponseModelCollection][horde_sdk.ai_horde_api.apimodels.collections.ResponseModelCollection] |
| `/v2/collections/{collection_id}` | `PATCH` | [UpdateCollectionRequest][horde_sdk.ai_horde_api.apimodels.collections.UpdateCollectionRequest] | 200 | [UpdateCollectionResponse][horde_sdk.ai_horde_api.apimodels.collections.UpdateCollectionResponse] |
| `/v2/documents/privacy` | `GET` | [AIHordeGetPrivacyPolicyRequest][horde_sdk.ai_horde_api.apimodels.documents.AIHordeGetPrivacyPolicyRequest] | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels.documents.HordeDocument] |
| `/v2/documents/sponsors` | `GET` | [AIHordeGetSponsorsRequest][horde_sdk.ai_horde_api.apimodels.documents.AIHordeGetSponsorsRequest] | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels.documents.HordeDocument] |
| `/v2/documents/terms` | `GET` | [AIHordeGetTermsRequest][horde_sdk.ai_horde_api.apimodels.documents.AIHordeGetTermsRequest] | 200 | [HordeDocument][horde_sdk.ai_horde_api.apimodels.documents.HordeDocument] |
| `/v2/filters` | `GET` | [FiltersListRequest][horde_sdk.ai_horde_api.apimodels.filters.FiltersListRequest] | 200 | [FiltersListResponse][horde_sdk.ai_horde_api.apimodels.filters.FiltersListResponse] |
| `/v2/filters` | `POST` | [FilterPromptSuspicionRequest][horde_sdk.ai_horde_api.apimodels.filters.FilterPromptSuspicionRequest] | 200 | [FilterPromptSuspicionResponse][horde_sdk.ai_horde_api.apimodels.filters.FilterPromptSuspicionResponse] |
| `/v2/filters` | `PUT` | [PutNewFilterRequest][horde_sdk.ai_horde_api.apimodels.filters.PutNewFilterRequest] | 201 | [FilterDetails][horde_sdk.ai_horde_api.apimodels.filters.FilterDetails] |
| `/v2/filters/regex` | `GET` | [FilterRegexRequest][horde_sdk.ai_horde_api.apimodels.filters.FilterRegexRequest] | 200 | [FilterRegexResponse][horde_sdk.ai_horde_api.apimodels.filters.FilterRegexResponse] |
| `/v2/filters/{filter_id}` | `DELETE` | [DeleteFilterRequest][horde_sdk.ai_horde_api.apimodels.filters.DeleteFilterRequest] | 200 | [DeleteFilterResponse][horde_sdk.ai_horde_api.apimodels.filters.DeleteFilterResponse] |
| `/v2/filters/{filter_id}` | `GET` | [SingleFilterRequest][horde_sdk.ai_horde_api.apimodels.filters.SingleFilterRequest] | 200 | [FilterDetails][horde_sdk.ai_horde_api.apimodels.filters.FilterDetails] |
| `/v2/filters/{filter_id}` | `PATCH` | [PatchExistingFilter][horde_sdk.ai_horde_api.apimodels.filters.PatchExistingFilter] | 200 | [FilterDetails][horde_sdk.ai_horde_api.apimodels.filters.FilterDetails] |
| `/v2/find_user` | `GET` | [FindUserRequest][horde_sdk.ai_horde_api.apimodels.find_user.FindUserRequest] | 200 | [UserDetailsResponse][horde_sdk.ai_horde_api.apimodels.users.UserDetailsResponse] |
| `/v2/generate/async` | `POST` | [ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.async_.ImageGenerateAsyncRequest] | 200 | [ImageGenerateAsyncDryRunResponse][horde_sdk.ai_horde_api.apimodels.generate.async_.ImageGenerateAsyncDryRunResponse] |
| `/v2/generate/async` | `POST` | [ImageGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.async_.ImageGenerateAsyncRequest] | 202 | [ImageGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate.async_.ImageGenerateAsyncResponse] |
| `/v2/generate/check/{id}` | `GET` | [ImageGenerateCheckRequest][horde_sdk.ai_horde_api.apimodels.generate.check.ImageGenerateCheckRequest] | 200 | [ImageGenerateCheckResponse][horde_sdk.ai_horde_api.apimodels.generate.check.ImageGenerateCheckResponse] |
| `/v2/generate/pop` | `POST` | [ImageGenerateJobPopRequest][horde_sdk.ai_horde_api.apimodels.generate.pop.ImageGenerateJobPopRequest] | 200 | [ImageGenerateJobPopResponse][horde_sdk.ai_horde_api.apimodels.generate.pop.ImageGenerateJobPopResponse] |
| `/v2/generate/rate/{id}` | `POST` | [RateRequest][horde_sdk.ai_horde_api.apimodels.generate.rate.RateRequest] | 200 | [RateResponse][horde_sdk.ai_horde_api.apimodels.generate.rate.RateResponse] |
| `/v2/generate/status/{id}` | `DELETE` | [DeleteImageGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate.status.DeleteImageGenerateRequest] | 200 | [ImageGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate.status.ImageGenerateStatusResponse] |
| `/v2/generate/status/{id}` | `GET` | [ImageGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate.status.ImageGenerateStatusRequest] | 200 | [ImageGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate.status.ImageGenerateStatusResponse] |
| `/v2/generate/submit` | `POST` | [ImageGenerationJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.generate.submit.ImageGenerationJobSubmitRequest] | 200 | [JobSubmitResponse][horde_sdk.ai_horde_api.apimodels.base.JobSubmitResponse] |
| `/v2/generate/text/async` | `POST` | [TextGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.text.async_.TextGenerateAsyncRequest] | 200 | [TextGenerateAsyncDryRunResponse][horde_sdk.ai_horde_api.apimodels.generate.text.async_.TextGenerateAsyncDryRunResponse] |
| `/v2/generate/text/async` | `POST` | [TextGenerateAsyncRequest][horde_sdk.ai_horde_api.apimodels.generate.text.async_.TextGenerateAsyncRequest] | 202 | [TextGenerateAsyncResponse][horde_sdk.ai_horde_api.apimodels.generate.text.async_.TextGenerateAsyncResponse] |
| `/v2/generate/text/pop` | `POST` | [TextGenerateJobPopRequest][horde_sdk.ai_horde_api.apimodels.generate.text.pop.TextGenerateJobPopRequest] | 200 | [TextGenerateJobPopResponse][horde_sdk.ai_horde_api.apimodels.generate.text.pop.TextGenerateJobPopResponse] |
| `/v2/generate/text/status/{id}` | `DELETE` | [DeleteTextGenerateRequest][horde_sdk.ai_horde_api.apimodels.generate.text.status.DeleteTextGenerateRequest] | 200 | [TextGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate.text.status.TextGenerateStatusResponse] |
| `/v2/generate/text/status/{id}` | `GET` | [TextGenerateStatusRequest][horde_sdk.ai_horde_api.apimodels.generate.text.status.TextGenerateStatusRequest] | 200 | [TextGenerateStatusResponse][horde_sdk.ai_horde_api.apimodels.generate.text.status.TextGenerateStatusResponse] |
| `/v2/generate/text/submit` | `POST` | [TextGenerationJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.generate.text.submit.TextGenerationJobSubmitRequest] | 200 | [JobSubmitResponse][horde_sdk.ai_horde_api.apimodels.base.JobSubmitResponse] |
| `/v2/interrogate/async` | `POST` | [AlchemyAsyncRequest][horde_sdk.ai_horde_api.apimodels.alchemy.async_.AlchemyAsyncRequest] | 202 | [AlchemyAsyncResponse][horde_sdk.ai_horde_api.apimodels.alchemy.async_.AlchemyAsyncResponse] |
| `/v2/interrogate/pop` | `POST` | [AlchemyPopRequest][horde_sdk.ai_horde_api.apimodels.alchemy.pop.AlchemyPopRequest] | 200 | [AlchemyJobPopResponse][horde_sdk.ai_horde_api.apimodels.alchemy.pop.AlchemyJobPopResponse] |
| `/v2/interrogate/status/{id}` | `DELETE` | [AlchemyDeleteRequest][horde_sdk.ai_horde_api.apimodels.alchemy.status.AlchemyDeleteRequest] | 200 | [AlchemyStatusResponse][horde_sdk.ai_horde_api.apimodels.alchemy.status.AlchemyStatusResponse] |
| `/v2/interrogate/status/{id}` | `GET` | [AlchemyStatusRequest][horde_sdk.ai_horde_api.apimodels.alchemy.status.AlchemyStatusRequest] | 200 | [AlchemyStatusResponse][horde_sdk.ai_horde_api.apimodels.alchemy.status.AlchemyStatusResponse] |
| `/v2/interrogate/submit` | `POST` | [AlchemyJobSubmitRequest][horde_sdk.ai_horde_api.apimodels.alchemy.submit.AlchemyJobSubmitRequest] | 200 | [AlchemyJobSubmitResponse][horde_sdk.ai_horde_api.apimodels.alchemy.submit.AlchemyJobSubmitResponse] |
| `/v2/kudos/award` | `POST` | [KudosAwardRequest][horde_sdk.ai_horde_api.apimodels.kudos.KudosAwardRequest] | 200 | [KudosAwardResponse][horde_sdk.ai_horde_api.apimodels.kudos.KudosAwardResponse] |
| `/v2/kudos/transfer` | `POST` | [KudosTransferRequest][horde_sdk.ai_horde_api.apimodels.kudos.KudosTransferRequest] | 200 | [KudosTransferResponse][horde_sdk.ai_horde_api.apimodels.kudos.KudosTransferResponse] |
| `/v2/operations/block_worker_ipaddr/{worker_id}` | `DELETE` | [DeleteWorkerIPAddressRequest][horde_sdk.ai_horde_api.apimodels.operations.DeleteWorkerIPAddressRequest] | 200 | [DeleteWorkerIPAddressResponse][horde_sdk.ai_horde_api.apimodels.operations.DeleteWorkerIPAddressResponse] |
| `/v2/operations/block_worker_ipaddr/{worker_id}` | `PUT` | [BlockWorkerIPAddressRequest][horde_sdk.ai_horde_api.apimodels.operations.BlockWorkerIPAddressRequest] | 200 | [BlockWorkerIPAddressResponse][horde_sdk.ai_horde_api.apimodels.operations.BlockWorkerIPAddressResponse] |
| `/v2/operations/ipaddr` | `DELETE` | [DeleteIPAddressRequest][horde_sdk.ai_horde_api.apimodels.operations.DeleteIPAddressRequest] | 200 | [DeleteIPAddressResponse][horde_sdk.ai_horde_api.apimodels.operations.DeleteIPAddressResponse] |
| `/v2/operations/ipaddr` | `GET` | [AllIPTimeoutsRequest][horde_sdk.ai_horde_api.apimodels.operations.AllIPTimeoutsRequest] | 200 | [IPTimeoutListResponse][horde_sdk.ai_horde_api.apimodels.operations.IPTimeoutListResponse] |
| `/v2/operations/ipaddr` | `GET` | [SingleIPTimeoutsRequest][horde_sdk.ai_horde_api.apimodels.operations.SingleIPTimeoutsRequest] | 200 | [IPTimeoutListResponse][horde_sdk.ai_horde_api.apimodels.operations.IPTimeoutListResponse] |
| `/v2/operations/ipaddr` | `POST` | [BlockIPAddressRequest][horde_sdk.ai_horde_api.apimodels.operations.BlockIPAddressRequest] | 200 | [BlockIPAddressResponse][horde_sdk.ai_horde_api.apimodels.operations.BlockIPAddressResponse] |
| `/v2/sharedkeys` | `PUT` | [SharedKeyCreateRequest][horde_sdk.ai_horde_api.apimodels.sharedkeys.SharedKeyCreateRequest] | 200 | [ExpiryStrSharedKeyDetailsResponse][horde_sdk.ai_horde_api.apimodels.sharedkeys.ExpiryStrSharedKeyDetailsResponse] |
| `/v2/sharedkeys/{sharedkey_id}` | `DELETE` | [SharedKeyDeleteRequest][horde_sdk.ai_horde_api.apimodels.sharedkeys.SharedKeyDeleteRequest] | 200 | [SharedKeyDeleteResponse][horde_sdk.ai_horde_api.apimodels.sharedkeys.SharedKeyDeleteResponse] |
| `/v2/sharedkeys/{sharedkey_id}` | `GET` | [SharedKeyDetailsRequest][horde_sdk.ai_horde_api.apimodels.sharedkeys.SharedKeyDetailsRequest] | 200 | [ExpiryStrSharedKeyDetailsResponse][horde_sdk.ai_horde_api.apimodels.sharedkeys.ExpiryStrSharedKeyDetailsResponse] |
| `/v2/sharedkeys/{sharedkey_id}` | `PATCH` | [SharedKeyModifyRequest][horde_sdk.ai_horde_api.apimodels.sharedkeys.SharedKeyModifyRequest] | 200 | [ExpiryStrSharedKeyDetailsResponse][horde_sdk.ai_horde_api.apimodels.sharedkeys.ExpiryStrSharedKeyDetailsResponse] |
| `/v2/stats/img/models` | `GET` | [ImageStatsModelsRequest][horde_sdk.ai_horde_api.apimodels.stats.ImageStatsModelsRequest] | 200 | [ImageStatsModelsResponse][horde_sdk.ai_horde_api.apimodels.stats.ImageStatsModelsResponse] |
| `/v2/stats/img/totals` | `GET` | [ImageStatsModelsTotalRequest][horde_sdk.ai_horde_api.apimodels.stats.ImageStatsModelsTotalRequest] | 200 | [ImageStatsModelsTotalResponse][horde_sdk.ai_horde_api.apimodels.stats.ImageStatsModelsTotalResponse] |
| `/v2/stats/text/models` | `GET` | [TextStatsModelsRequest][horde_sdk.ai_horde_api.apimodels.stats.TextStatsModelsRequest] | 200 | [TextStatsModelResponse][horde_sdk.ai_horde_api.apimodels.stats.TextStatsModelResponse] |
| `/v2/stats/text/totals` | `GET` | [TextStatsModelsTotalRequest][horde_sdk.ai_horde_api.apimodels.stats.TextStatsModelsTotalRequest] | 200 | [TextStatsModelsTotalResponse][horde_sdk.ai_horde_api.apimodels.stats.TextStatsModelsTotalResponse] |
| `/v2/status/heartbeat` | `GET` | [AIHordeHeartbeatRequest][horde_sdk.ai_horde_api.apimodels.status.AIHordeHeartbeatRequest] | 200 | [AIHordeHeartbeatResponse][horde_sdk.ai_horde_api.apimodels.status.AIHordeHeartbeatResponse] |
| `/v2/status/models` | `GET` | [HordeStatusModelsAllRequest][horde_sdk.ai_horde_api.apimodels.status.HordeStatusModelsAllRequest] | 200 | [HordeStatusModelsAllResponse][horde_sdk.ai_horde_api.apimodels.status.HordeStatusModelsAllResponse] |
| `/v2/status/models/{model_name}` | `GET` | [HordeStatusModelsSingleRequest][horde_sdk.ai_horde_api.apimodels.status.HordeStatusModelsSingleRequest] | 200 | [HordeStatusModelsSingleResponse][horde_sdk.ai_horde_api.apimodels.status.HordeStatusModelsSingleResponse] |
| `/v2/status/news` | `GET` | [NewsRequest][horde_sdk.ai_horde_api.apimodels.status.NewsRequest] | 200 | [NewsResponse][horde_sdk.ai_horde_api.apimodels.status.NewsResponse] |
| `/v2/status/performance` | `GET` | [HordePerformanceRequest][horde_sdk.ai_horde_api.apimodels.status.HordePerformanceRequest] | 200 | [HordePerformanceResponse][horde_sdk.ai_horde_api.apimodels.status.HordePerformanceResponse] |
| `/v2/status/sampler_constraints` | `GET` | [SamplerConstraintsRequest][horde_sdk.ai_horde_api.apimodels.status.SamplerConstraintsRequest] | 200 | [SamplerConstraintsResponse][horde_sdk.ai_horde_api.apimodels.status.SamplerConstraintsResponse] |
| `/v2/styles/image` | `GET` | [AllStylesImageRequest][horde_sdk.ai_horde_api.apimodels.styles.AllStylesImageRequest] | 200 | [AllStylesImageResponse][horde_sdk.ai_horde_api.apimodels.styles.AllStylesImageResponse] |
| `/v2/styles/image` | `POST` | [CreateStyleImageRequest][horde_sdk.ai_horde_api.apimodels.styles.CreateStyleImageRequest] | 200 | [ModifyStyleImageResponse][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleImageResponse] |
| `/v2/styles/image/{style_id}` | `DELETE` | [DeleteStyleImageRequest][horde_sdk.ai_horde_api.apimodels.styles.DeleteStyleImageRequest] | 200 | [DeleteStyleImageResponse][horde_sdk.ai_horde_api.apimodels.styles.DeleteStyleImageResponse] |
| `/v2/styles/image/{style_id}` | `GET` | [SingleStyleImageByIDRequest][horde_sdk.ai_horde_api.apimodels.styles.SingleStyleImageByIDRequest] | 200 | [StyleStable][horde_sdk.ai_horde_api.apimodels.styles.StyleStable] |
| `/v2/styles/image/{style_id}` | `PATCH` | [ModifyStyleImageRequest][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleImageRequest] | 200 | [ModifyStyleImageResponse][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleImageResponse] |
| `/v2/styles/image/{style_id}/example` | `POST` | [StyleImageExampleAddRequest][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleAddRequest] | 200 | [StyleImageExampleModifyResponse][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleModifyResponse] |
| `/v2/styles/image/{style_id}/example/{example_id}` | `DELETE` | [StyleImageExampleDeleteRequest][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleDeleteRequest] | 200 | [StyleImageExampleDeleteResponse][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleDeleteResponse] |
| `/v2/styles/image/{style_id}/example/{example_id}` | `PATCH` | [StyleImageExampleModifyRequest][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleModifyRequest] | 200 | [StyleImageExampleModifyResponse][horde_sdk.ai_horde_api.apimodels.styles.StyleImageExampleModifyResponse] |
| `/v2/styles/image_by_name/{style_name}` | `GET` | [SingleStyleImageByNameRequest][horde_sdk.ai_horde_api.apimodels.styles.SingleStyleImageByNameRequest] | 200 | [StyleStable][horde_sdk.ai_horde_api.apimodels.styles.StyleStable] |
| `/v2/styles/text` | `GET` | [AllStylesTextRequest][horde_sdk.ai_horde_api.apimodels.styles.AllStylesTextRequest] | 200 | [AllStylesTextResponse][horde_sdk.ai_horde_api.apimodels.styles.AllStylesTextResponse] |
| `/v2/styles/text` | `POST` | [CreateStyleTextRequest][horde_sdk.ai_horde_api.apimodels.styles.CreateStyleTextRequest] | 200 | [ModifyStyleTextResponse][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleTextResponse] |
| `/v2/styles/text/{style_id}` | `DELETE` | [DeleteStyleTextRequest][horde_sdk.ai_horde_api.apimodels.styles.DeleteStyleTextRequest] | 200 | [DeleteStyleTextResponse][horde_sdk.ai_horde_api.apimodels.styles.DeleteStyleTextResponse] |
| `/v2/styles/text/{style_id}` | `GET` | [SingleStyleTextByIDRequest][horde_sdk.ai_horde_api.apimodels.styles.SingleStyleTextByIDRequest] | 200 | [StyleKobold][horde_sdk.ai_horde_api.apimodels.styles.StyleKobold] |
| `/v2/styles/text/{style_id}` | `PATCH` | [ModifyStyleTextRequest][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleTextRequest] | 200 | [ModifyStyleTextResponse][horde_sdk.ai_horde_api.apimodels.styles.ModifyStyleTextResponse] |
| `/v2/styles/text_by_name/{style_name}` | `GET` | [SingleStyleTextByNameRequest][horde_sdk.ai_horde_api.apimodels.styles.SingleStyleTextByNameRequest] | 200 | [StyleKobold][horde_sdk.ai_horde_api.apimodels.styles.StyleKobold] |
| `/v2/teams` | `GET` | [AllTeamDetailsRequest][horde_sdk.ai_horde_api.apimodels.teams.AllTeamDetailsRequest] | 200 | [AllTeamDetailsResponse][horde_sdk.ai_horde_api.apimodels.teams.AllTeamDetailsResponse] |
| `/v2/teams` | `POST` | [CreateTeamRequest][horde_sdk.ai_horde_api.apimodels.teams.CreateTeamRequest] | 200 | [ModifyTeam][horde_sdk.ai_horde_api.apimodels.teams.ModifyTeam] |
| `/v2/teams/{team_id}` | `DELETE` | [DeleteTeamRequest][horde_sdk.ai_horde_api.apimodels.teams.DeleteTeamRequest] | 200 | [DeleteTeamResponse][horde_sdk.ai_horde_api.apimodels.teams.DeleteTeamResponse] |
| `/v2/teams/{team_id}` | `GET` | [SingleTeamDetailsRequest][horde_sdk.ai_horde_api.apimodels.teams.SingleTeamDetailsRequest] | 200 | [TeamDetails][horde_sdk.ai_horde_api.apimodels.teams.TeamDetails] |
| `/v2/teams/{team_id}` | `PATCH` | [ModifyTeamRequest][horde_sdk.ai_horde_api.apimodels.teams.ModifyTeamRequest] | 200 | [ModifyTeam][horde_sdk.ai_horde_api.apimodels.teams.ModifyTeam] |
| `/v2/users` | `GET` | [ListUsersDetailsRequest][horde_sdk.ai_horde_api.apimodels.users.ListUsersDetailsRequest] | 200 | [ListUsersDetailsResponse][horde_sdk.ai_horde_api.apimodels.users.ListUsersDetailsResponse] |
| `/v2/users/{user_id}` | `DELETE` | [DeleteUserRequest][horde_sdk.ai_horde_api.apimodels.users.DeleteUserRequest] | 200 | [DeleteUserResponse][horde_sdk.ai_horde_api.apimodels.users.DeleteUserResponse] |
| `/v2/users/{user_id}` | `GET` | [SingleUserDetailsRequest][horde_sdk.ai_horde_api.apimodels.users.SingleUserDetailsRequest] | 200 | [UserDetailsResponse][horde_sdk.ai_horde_api.apimodels.users.UserDetailsResponse] |
| `/v2/users/{user_id}` | `PUT` | [ModifyUserRequest][horde_sdk.ai_horde_api.apimodels.users.ModifyUserRequest] | 200 | [ModifyUserResponse][horde_sdk.ai_horde_api.apimodels.users.ModifyUserResponse] |
| `/v2/workers` | `GET` | [AllWorkersDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers.workers.AllWorkersDetailsRequest] | 200 | [AllWorkersDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers.workers.AllWorkersDetailsResponse] |
| `/v2/workers/messages` | `GET` | [AllWorkerMessagesRequest][horde_sdk.ai_horde_api.apimodels.workers.messages.AllWorkerMessagesRequest] | 200 | [ResponseModelMessages][horde_sdk.ai_horde_api.apimodels.workers.messages.ResponseModelMessages] |
| `/v2/workers/messages` | `POST` | [CreateWorkerMessageRequest][horde_sdk.ai_horde_api.apimodels.workers.messages.CreateWorkerMessageRequest] | 200 | [ResponseModelMessage][horde_sdk.ai_horde_api.apimodels.workers.messages.ResponseModelMessage] |
| `/v2/workers/messages/{message_id}` | `DELETE` | [DeleteWorkerMessageRequest][horde_sdk.ai_horde_api.apimodels.workers.messages.DeleteWorkerMessageRequest] | 200 | [DeleteWorkerMessageResponse][horde_sdk.ai_horde_api.apimodels.workers.messages.DeleteWorkerMessageResponse] |
| `/v2/workers/messages/{message_id}` | `GET` | [SingleWorkerMessageRequest][horde_sdk.ai_horde_api.apimodels.workers.messages.SingleWorkerMessageRequest] | 200 | [ResponseModelMessage][horde_sdk.ai_horde_api.apimodels.workers.messages.ResponseModelMessage] |
| `/v2/workers/name/{worker_name}` | `GET` | [SingleWorkerNameDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers.workers.SingleWorkerNameDetailsRequest] | 200 | [SingleWorkerDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers.workers.SingleWorkerDetailsResponse] |
| `/v2/workers/{worker_id}` | `DELETE` | [DeleteWorkerRequest][horde_sdk.ai_horde_api.apimodels.workers.workers.DeleteWorkerRequest] | 200 | [DeleteWorkerResponse][horde_sdk.ai_horde_api.apimodels.workers.workers.DeleteWorkerResponse] |
| `/v2/workers/{worker_id}` | `GET` | [SingleWorkerDetailsRequest][horde_sdk.ai_horde_api.apimodels.workers.workers.SingleWorkerDetailsRequest] | 200 | [SingleWorkerDetailsResponse][horde_sdk.ai_horde_api.apimodels.workers.workers.SingleWorkerDetailsResponse] |
| `/v2/workers/{worker_id}` | `PUT` | [ModifyWorkerRequest][horde_sdk.ai_horde_api.apimodels.workers.workers.ModifyWorkerRequest] | 200 | [ModifyWorkerResponse][horde_sdk.ai_horde_api.apimodels.workers.workers.ModifyWorkerResponse] |
<!-- END GENERATED: endpoint-map -->

## Code map

| Responsibility | Module | Symbol |
| --- | --- | --- |
| Request discovery | `horde_sdk/generic_api/_reflection.py` | `get_all_request_types` |
| Request metadata | `horde_sdk/generic_api/apimodels.py` | `HordeRequest` |
| Table generation | `docs/build_docs.py` | `collect_endpoint_rows` |

The live Swagger parity test validates the same request metadata without writing documentation artifacts.
