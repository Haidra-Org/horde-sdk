---
title: "Logging reference"
summary: "Describe SDK logger setup, progress and completion levels, and sensitive-field handling."
status: stub
topics: [errors, utilities]
order: 180
---

# Logging reference

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [errors](../topics.md#errors), [utilities](../topics.md#utilities)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Logger labels and setup live in `horde_sdk.horde_logging`. API models can exclude
sensitive fields from logs through `get_extra_fields_to_exclude_from_log`; source images and credentials must not be
added back by application logging.
