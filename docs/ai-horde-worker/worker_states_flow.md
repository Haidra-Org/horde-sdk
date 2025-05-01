# Worker States Flow

This is visual depiction of the `base_generate_progress_transitions` map found in `horde_sdk/ai_horde_worker/consts.py`.

You should also see the [worker loop](../haidra-assets/docs/worker_loop.md) and [job lifecycle explanation](../haidra-assets/docs/workers.md) for additional details.

```mermaid
flowchart TD
    %% Style definitions
    classDef error stroke:#f00,stroke-dasharray: 2 2

    %% Main flow
    NOT_STARTED --> PRELOADING
    NOT_STARTED --> GENERATING
    NOT_STARTED --> PENDING_POST_PROCESSING
    NOT_STARTED --> POST_PROCESSING
    NOT_STARTED -.-> ERROR:::error

    PRELOADING --> PRELOADING_COMPLETE
    PRELOADING -.-> ERROR:::error

    PRELOADING_COMPLETE --> GENERATING
    PRELOADING_COMPLETE --> PENDING_POST_PROCESSING
    PRELOADING_COMPLETE --> POST_PROCESSING
    PRELOADING_COMPLETE -.-> ERROR:::error

    GENERATING --> PENDING_POST_PROCESSING
    GENERATING --> POST_PROCESSING
    GENERATING --> PENDING_SAFETY_CHECK
    GENERATING --> SAFETY_CHECKING
    GENERATING -.-> ERROR:::error

    PENDING_POST_PROCESSING --> POST_PROCESSING
    PENDING_POST_PROCESSING -.-> ERROR:::error

    POST_PROCESSING --> PENDING_SAFETY_CHECK
    POST_PROCESSING --> SAFETY_CHECKING
    POST_PROCESSING -.-> ERROR:::error

    PENDING_SAFETY_CHECK --> SAFETY_CHECKING
    PENDING_SAFETY_CHECK -.-> ERROR:::error

    SAFETY_CHECKING --> PENDING_SUBMIT
    SAFETY_CHECKING -.-> ERROR:::error

    PENDING_SUBMIT --> SUBMITTING
    PENDING_SUBMIT -.-> ERROR:::error

    SUBMITTING --> SUBMIT_COMPLETE
    SUBMITTING --> ABANDONED
    SUBMITTING -.-> ERROR:::error

    SUBMIT_COMPLETE --> COMPLETE

    ERROR --> ABORTED

    ABORTED --> REPORTED_FAILED
    ABORTED -.-> ERROR:::error

    USER_REQUESTED_ABORT --> USER_ABORT_COMPLETE
    USER_REQUESTED_ABORT --> ABANDONED
```
