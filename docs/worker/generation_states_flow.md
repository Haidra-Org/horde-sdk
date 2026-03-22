# Generation States Flow

## Typical States Flow

This is visual depiction of the `base_generate_progress_transitions` map found in `horde_sdk/worker/consts.py`.

You should also see the [worker loop](../haidra-assets/docs/worker_loop.md) and [job lifecycle explanation](../haidra-assets/docs/workers.md) for additional details.

```mermaid
---
title: Worker States Flow (without error states)
---
flowchart TD

    NOT_STARTED@{shape: subproc}
    PRELOADING@{shape: subproc}
    PRELOADING_COMPLETE@{shape: subproc}
    PENDING_POST_PROCESSING@{ shape: subproc}
    POST_PROCESSING@{ shape: subproc}
    GENERATING@{ shape: subproc}
    PENDING_SAFETY_CHECK@{ shape: subproc}
    SAFETY_CHECKING@{ shape: subproc}
    PENDING_SUBMIT@{ shape: subproc}
    SUBMITTING@{ shape: subproc}
    SUBMIT_COMPLETE@{ shape: subproc}
    COMPLETE@{ shape: subproc}

    NOT_STARTED --> D1
    D1@{label: "Is preloading required?" }
    D2@{label: "Is generation required?" }
    D3@{label: "Is post-processing required?" }
    D1 -->|Yes| PRELOADING
    D1 -->|No| D2
    D2 -->|Yes| GENERATING
    D2 -->|No| D3
    D3 -->|Yes| PENDING_POST_PROCESSING
    D3 -->|No| PENDING_SAFETY_CHECK


    PRELOADING --> PRELOADING_COMPLETE

    PRELOADING_COMPLETE --> D2

    GENERATING --> D3

    PENDING_POST_PROCESSING--> POST_PROCESSING

    POST_PROCESSING --> D11@{label: "Is safety check required?" }
    D11 -->|Yes| PENDING_SAFETY_CHECK
    D11 -->|No| D12@{label: "Is submit required?" }

    PENDING_SAFETY_CHECK --> SAFETY_CHECKING

    SAFETY_CHECKING --> D12
    D12 -->|Yes| PENDING_SUBMIT
    D12 -->|No| COMPLETE

    PENDING_SUBMIT --> SUBMITTING

    SUBMITTING --> SUBMIT_COMPLETE

    SUBMIT_COMPLETE --> COMPLETE

    linkStyle 1 stroke:#27ae60,stroke-width:3px,color:#27ae60
    linkStyle 2 stroke:#e74c3c,stroke-width:3px
    linkStyle 3 stroke:#27ae60,stroke-width:3px,color:#27ae60
    linkStyle 4 stroke:#e74c3c,stroke-width:3px
    linkStyle 5 stroke:#27ae60,stroke-width:3px,color:#27ae60
    linkStyle 6 stroke:#e74c3c,stroke-width:3px
    linkStyle 12 stroke:#27ae60,stroke-width:3px,color:#27ae60
    linkStyle 13 stroke:#e74c3c,stroke-width:3px
    linkStyle 16 stroke:#27ae60,stroke-width:3px,color:#27ae60
    linkStyle 17 stroke:#e74c3c,stroke-width:3px

```

---

```mermaid
---
title: Worker Error States Flow
---

flowchart TD
    style ERROR stroke-dasharray: 5 5
    style ABORTED stroke-dasharray: 5 5
    style USER_REQUESTED_ABORT stroke-dasharray: 5 5

    ERROR["`Error
    (_valid from all states_)`"] --> ABORTED
    ERROR --> ABANDONED

    ABORTED["`Aborted
    (_valid from all states_)`"] --> REPORTED_FAILED
    ABORTED --> ERROR

    USER_REQUESTED_ABORT["`User Requested Abort
    (_valid from all states_)`"] --> USER_ABORT_COMPLETE

    REPORTED_FAILED

    USER_ABORT_COMPLETE

    ABANDONED

```

---

`ERROR`, `ABORTED` and `USER_REQUESTED_ABORT` states are always valid to transition to. If transitioning to `ERROR`, it is **only** permissible to transition to the state from which the error occurred, or to `ABORTED`. If transitioning to `ABORTED`, it is only permissible to transition to `REPORTED_FAILED` or `USER_REQUESTED_ABORT`.

Consider the following good and bad examples of error transitions:

Good:

- `NOT_STARTED` -> `PRELOADING` -> `ERROR` -> `PRELOADING` -> `PRELOADING_COMPLETE` -> ...
    - In this case, the error occurred during preloading, and the worker was able to recover and continue.
- `NOT_STARTED` -> `PRELOADING` -> `ERROR` -> `PRELOADING` -> `ERROR` -> `ABORTED` -> `REPORTED_FAILED`
    - Here, the worker encountered an error during preloading, attempted to recover, but failed again and then aborted the job. Note that you can set the intended number of retries in worker job configuration. See the `HordeWorkerJobConfig` class and the  `state_error_limits` arg in a generation class constructor for more details.
- `NOT_STARTED` -> `PRELOADING` -> `USER_REQUESTED_ABORT` -> `USER_ABORT_COMPLETE`
    - In this case, the user who created the job requested an abort, and the worker was able to complete the abort process successfully.

Bad:

- `NOT_STARTED` -> `PRELOADING` -> `ERROR` -> `GENERATING`
    - If an error occurs, you have to explicitly handle it and you must transition *back* to the state from which the error occurred, or to `ABORTED`. In this case, the worker is trying to continue generating after an error occurred during preloading, which is not allowed. The correct transition would be to go back to `PRELOADING` or to `ABORTED`.
- `NOT_STARTED` -> `PRELOADING` -> `ERROR` -> `ERROR`
    - This is not allowed, as you cannot transition to `ERROR` from `ERROR`. You must handle the error and transition to a valid state, such as `ABORTED` or back to the state from which the error occurred. If this situation occurs to you frequently, you will need to review your flow and control to ensure that errors and exceptions are handled properly. Consider checking the current state before transitioning to `ERROR` and if it is already `ERROR` consider logging the error and aborting the job instead.

## Black Box States Flow

Depending on the worker backend, it may not always be possible to track all of the states. For example, it may be that the backend silently handles `PRELOADING` without a callback or hook to detect that it has started or completed. Further, some backends may ever only support a single model, so `PRELOADING` may not be applicable at all. In these cases, it is appropriate to use `black_box_mode` for these `HordeSingleGeneration` class instances.

In this case, the flow is simplified to the following (where safety checks, even if required, are also an optional state)

---

```mermaid
---
title: Black Box States (not including error states)
---
flowchart TD
    NOT_STARTED --> GENERATING

    GENERATING --> PENDING_SUBMIT
    GENERATING --> PENDING_SAFETY_CHECK
    GENERATING --> COMPLETE

    PENDING_SAFETY_CHECK --> SAFETY_CHECKING

    SAFETY_CHECKING --> PENDING_SUBMIT
    SAFETY_CHECKING --> COMPLETE

    PENDING_SUBMIT --> SUBMITTING

    SUBMITTING --> SUBMIT_COMPLETE
    SUBMITTING --> COMPLETE

    SUBMIT_COMPLETE --> COMPLETE
```

---

```mermaid
---
title: Black Box Error States
---

flowchart TD
    style ERROR stroke-dasharray: 5 5
    style ABORTED stroke-dasharray: 5 5
    style USER_REQUESTED_ABORT stroke-dasharray: 5 5

    ERROR["`Error
    (_valid from all states_)`"] --> ABORTED
    ERROR --> ABANDONED

    ABORTED --> REPORTED_FAILED
    ABORTED --> ABANDONED

    USER_REQUESTED_ABORT["`User Requested Abort
    (_valid from all states_)`"] --> USER_ABORT_COMPLETE
    USER_REQUESTED_ABORT --> ABANDONED

    USER_ABORT_COMPLETE

    REPORTED_FAILED

    ABANDONED
```

---

Note that a generation may still require additional steps, such as post-processing or safety checking, but it is assumed that these steps are handled internally by the backend and do not require explicit state transitions in the worker. The worker will still report the final state as `COMPLETE` or `FAILED` based on the outcome of the generation. It is incumbent on the implementor to ensure that these steps have happened as intended.
