---
title: "Drive the worker generation state machine"
summary: "Advance a worker generation through preparation, execution, submission, and terminal cleanup."
topics: [backends, dispatch, generation, workers]
order: 80
---

# Drive the worker generation state machine

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [backends](../topics.md#backends), [dispatch](../topics.md#dispatch), [generation](../topics.md#generation), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

Construct the appropriate `HordeWorkerJob` and `HordeSingleGeneration` subtype after a successful pop. The generation
object owns one unit of backend work; the job coordinates one or more generations for the popped request.

1. Validate and normalize pop data before creating the generation. Verify the dispatch converter returns backend-ready
   parameters without mutating the API response model.
2. Start generation through the job/executor boundary. Observe its state transition and persist the Horde job ID.
3. Record progress only in states that permit it. Treat backend cancellation and exceptions as explicit terminal paths.
4. Submit the typed result, then mark the generation terminal only after the submit response succeeds.
5. Release backend resources in `finally`, including partial-output and cancellation paths.

Tests should assert the exact transition sequence and reject an illegal transition. A submitted generation cannot be
retracted; report a later failure as a new worker event. See [worker transitions](../reference/worker-transitions.md)
for the state contract and [the worker model](../explanation/worker-model.md) for ownership boundaries.
