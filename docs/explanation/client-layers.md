---
title: "Client layers and ownership"
summary: "Explain why the SDK separates transport, sessions, manual operations, and simple polling clients."
topics: [architecture, clients, requests]
order: 10
---

# Client layers and ownership

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [clients](../topics.md#clients), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

The SDK offers several clients because a convenient generation call and a controllable workflow engine require
different ownership boundaries. They share typed requests and responses while assigning polling, connection reuse, and
cleanup to different layers.

## From transport to workflow

The generic client layer serializes a `HordeRequest`, performs one HTTP exchange, and parses the selected response
type. AI Horde manual clients add endpoint-specific convenience methods. Session clients retain connection state and
track responses that require follow-up. Simple clients combine submission, polling, final retrieval, timeout policy,
and cleanup into one operation.

This layering keeps low-level extension possible without requiring every caller to reimplement the fragile request
lifecycle. Its cost is a larger public client family and some behavior inherited across modules, which is why the
[client matrix](../reference/client-behavior.md) presents ownership explicitly.

## Why simple is the default

Long-lived Horde requests remain server resources until final retrieval or deletion. A caller that only wants a result
should not need to persist IDs and reproduce cleanup rules. Simple clients make that safe path easy. Manual clients
remain available for durable schedulers that already have persistence and retry machinery.

Synchronous and asynchronous clients are parallel surfaces. The async variants share `aiohttp` sessions and avoid
blocking an event loop; they do not change request or response semantics.

The rejected alternative is one client with many mode flags. That design hides resource ownership at each call site
and permits invalid combinations. Separate types make the ownership choice visible in construction and type checking.
