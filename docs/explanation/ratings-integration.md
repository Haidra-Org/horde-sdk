---
title: "Ratings integration"
summary: "Explain the separate ratings-service boundary and how its client relates to generation results."
status: stub
topics: [architecture, ratings]
order: 130
---

# Ratings integration

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [ratings](../topics.md#ratings)
<!-- END GENERATED: topics -->

> **Not yet documented in full.** Ratings use a separate service client and model set under `horde_sdk.ratings_api`.
Generation identifiers connect domains, while endpoint and error behavior remain owned by the ratings service.
