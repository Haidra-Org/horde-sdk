---
title: "Typed request and response design"
summary: "Explain how Pydantic models bind Python types, wire aliases, endpoint metadata, and compatibility behavior."
topics: [api-models, architecture, requests]
order: 20
---

# Typed request and response design

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [api-models](../topics.md#api-models), [architecture](../topics.md#architecture), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

Horde SDK treats API operations as typed objects rather than loosely structured dictionaries. A request carries its
validated data and the metadata required to submit it; a response type expresses the contract expected for a success
status.

## Properties the design buys

Pydantic validation catches field bounds, combinations, and identifiers before network submission. Serialization
aliases preserve the API's names while Python fields follow repository conventions. Class-level endpoint metadata lets
generic clients submit new request types without endpoint-specific branches. Successful status mappings represent
operations such as dry runs and accepted async work without guessing from payload shape.

The cost is strictness at an evolving API boundary. Response models commonly allow unknown fields in production so a
new server field does not break an older SDK, while tests use stricter settings to expose model drift. Aliases accept
known historical names when the wire contract changes.

## Why dictionaries remain at the edge

Raw dictionaries are still the transport representation and may appear inside genuinely open-ended backend payloads.
They are converted at the nearest boundary. Allowing dictionaries throughout application code would move validation
to every consumer and weaken generated reference material.

The [request and response reference](../reference/request-response-contracts.md) specifies the class methods and mixins
that implement this design. The endpoint map demonstrates how the metadata composes across the full API.
