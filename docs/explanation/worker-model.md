---
title: "Worker jobs, generations, and state"
summary: "Explain how worker jobs coordinate popped requests while generations own individual backend results."
topics: [architecture, backends, generation, workers]
order: 40
---

# Worker jobs, generations, and state

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [architecture](../topics.md#architecture), [backends](../topics.md#backends), [generation](../topics.md#generation), [workers](../topics.md#workers)
<!-- END GENERATED: topics -->

One popped Horde request can ask for multiple results. The SDK represents the request as a worker job and each result
as a single generation so scheduling, progress, submission, and failure can be reasoned about at the correct unit.

The job owns shared pop metadata and coordinates generation objects. A generation owns the backend operation and its
state. Dispatch selects work and prepares parameters before generation starts; submit models translate terminal output
back to the Horde API.

## Failure isolation

Per-generation state permits partial success. One backend result can complete while another faults, and the job can
report each accurately. A single job-level state would be simpler but could only hide partial outcomes or encode them
as ad hoc collections.

Terminal state follows successful Horde submission rather than local backend completion. That ordering prevents a
worker from reporting completion before the distributed system has accepted the result. It also means submission
failure remains a first-class fault path after expensive local work has finished.

The [worker transition reference](../reference/worker-transitions.md) gives the state contract; the
[worker-state procedure](../how-to/drive-worker-state.md) applies it at an integration boundary.
