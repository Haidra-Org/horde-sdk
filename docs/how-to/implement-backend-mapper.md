---
title: "Implement a backend value mapper"
summary: "Normalize Horde-facing values at a backend boundary while preserving typed internal representations."
topics: [architecture, backends, generation]
order: 70
---

# Implement a backend value mapper

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [backends](../topics.md#backends), [generation](../topics.md#generation)
<!-- END GENERATED: topics -->

Use a mapper when Horde and a backend name the same value differently. Define the mapping at the conversion boundary,
keep the backend-native representation out of API models, and make unknown values explicit.

1. Identify the typed Horde field and the backend field in `horde_sdk.backend_parsing` or a dispatch converter.
2. Define a one-direction dictionary whose keys are accepted Horde values and whose values are backend-native values.
3. Convert in the backend adapter immediately before building its payload. Preserve `None` when omission has meaning;
   raise a targeted error when the backend cannot accept a supplied value.
4. Add parameterized tests for every known mapping, `None`, and one unknown value. Verify the emitted backend payload,
   rather than the dictionary alone.

Reverse conversion requires a separate mapping because backend aliases are rarely one-to-one. Removing a mapper means
moving its accepted values and failure policy to the replacement boundary in the same change. The
[backend normalization explanation](../explanation/backend-normalization.md) describes why conversion stays at the edge.
