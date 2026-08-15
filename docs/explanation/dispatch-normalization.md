---
title: "Dispatch normalization"
summary: "Explain how feature requirements, worker advertisements, and parameter conversion select executable work."
topics: [backends, dispatch, workers]
order: 110
---

# Dispatch normalization

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [backends](../topics.md#backends), [dispatch](../topics.md#dispatch), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

Dispatch receives protocol-specific jobs, describes their portable render requirements, checks those requirements
against a worker advertisement, and then converts accepted work to backend-independent generation parameters. These
are distinct lifecycle steps: a job can be valid at the wire boundary and still be deliberately degraded during
conversion when an optional input is unusable.

## One canonical feature vocabulary

`ImageGenerationFeatureFlags` is the canonical image feature set in both directions. A request-side instance contains
the features one generation requires. `ImageWorkerFeatureFlags.image_generation_feature_flags` contains the features
a worker supports. A second field-bearing requirements or capability model would duplicate the same vocabulary and is
not needed.

Compatibility is directional set inclusion:

- every requested baseline, sampler, scheduler, sampler solver knob, ControlNet type, post-processor,
  source-processing mode, workflow, and auxiliary-model source must be advertised by the worker;
- a requested boolean feature must be true in the worker profile;
- false, empty, or absent request fields add no requirement;
- absent optional collections in a worker profile advertise no support for that feature family;
- unknown string values compare exactly, so an older profile fails closed unless it explicitly advertises the value.

Requirements from a different generation domain return an `unsupported_generation_type` reason. They are never
treated as an empty compatible request.

`PerBaselineFeatureFlags` narrows the flat worker profile. `None` leaves the flat advertisement in effect. A supplied
map is exhaustive: an omitted requested baseline has no support in that map. This keeps partial maps from silently
widening a worker's capabilities.

The compatibility result covers portable render behavior only. Callers still compose model availability, numeric
limits, memory fit, queue and recovery state, transport support, and service or operator policy.

## Lifecycle-specific extraction

`image_job_pop_response_to_feature_flags()` reads an accepted AI-Horde pop response without model-reference refresh,
image decoding, or backend imports. The caller supplies the resolved model baseline when it is known. This is suitable
for checking the wire job before expensive normalization.

`image_parameters_to_feature_flags()` reads backend-independent `ImageGenerationParameters`. It describes the workload
that will actually execute, including exact auxiliary-model sources, precomputed ControlNet maps, custom-workflow text,
remix inputs, sampler solver knobs, flow shifting, transparent generation, and concrete post-processing operation
names.

The two results agree when conversion is lossless. They intentionally differ when fault-tolerant conversion selects a
different workload. For example, a source-processing request with no usable source image can become txt2img; the wire
feature set continues to describe the accepted request while the parameter feature set describes the fallback.

## Combining worker support

`union_image_generation_feature_flags()` combines each feature axis independently.
`intersect_image_generation_feature_flags()` keeps only values common to every supplied profile. Both operate on the
canonical model and deliberately exclude resources, models, numeric limits, and scheduling policy. An intersection
with no common baseline is rejected because `ImageGenerationFeatureFlags` represents an executable image feature set,
not an empty worker.

`union_image_worker_feature_flags()` combines complete worker profiles axis by axis. It unions the canonical generation feature
sets and preserves exhaustive per-baseline semantics. When any member restricts an axis, the result computes that
axis for every advertised baseline; an unrestricted member contributes its flat values only on the baselines that
member advertises. Rebuilding those maps from flattened booleans would lose which member can serve which baseline.
The result does not preserve correlations between separate axes: for example, a model or sampler from one member can
be combined with a feature contributed by another. A caller emitting work offers must retain member identity or prove
that the combined externally visible fields are equivalent; an axis-wise union alone is not a routeability proof.

## AI Horde worker advertisements

`image_worker_bridge_data_to_feature_flags()` narrows an implementation profile with validated operator choices.
Configuration is policy and cannot invent exact backend support. `apply_image_worker_feature_flags_to_pop_request()`
then projects the effective canonical profile onto the AI Horde's coarse image-pop booleans while retaining request
identity, model, policy, and numeric fields. Source-image and ControlNet bits include implicit workflow requirements;
the SDXL bit requires SDXL support; and the all-extended bit is emitted only when every control type currently behind
that protocol bit is supported. Runtime readiness and pressure may narrow those projected booleans further.
