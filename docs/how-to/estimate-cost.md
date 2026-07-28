---
title: "Estimate request cost"
summary: "Use dry-run request variants to obtain current kudos estimates without creating generation jobs."
topics: [clients, generation, requests]
order: 40
---

# Estimate request cost

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [generation](../topics.md#generation), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Set `dry_run=True` on an image or text async request, then submit it through the matching simple-client dry-run method.
The API evaluates current pricing and returns `kudos` without creating a job.

```python
request = image_request().model_copy(update={"dry_run": True})
estimate = AIHordeAPISimpleClient().image_generate_request_dry_run(request)
print(estimate.kudos)
```

Verify that the response is `ImageGenerateAsyncDryRunResponse` or `TextGenerateAsyncDryRunResponse` and contains a
non-negative `kudos` value. The estimate is point-in-time data; worker availability and pricing can change before live
submission.

Dry-run calls require network access but need no cleanup because they create no follow-up resource. To return to live
behavior, construct a new request with `dry_run=False`; avoid mutating and reusing a request shared across tasks.
