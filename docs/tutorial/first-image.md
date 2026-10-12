---
title: "Create and verify your first image"
summary: "Estimate, submit, download, and verify one anonymous image request with the synchronous simple client."
topics: [clients, generation, images, requests]
order: 10
---

# Create and verify your first image

<!-- BEGIN GENERATED: topics (gen_doc_index.py) -->
Topics: [clients](../topics.md#clients), [generation](../topics.md#generation), [images](../topics.md#images), [requests](../topics.md#requests)
<!-- END GENERATED: topics -->

This lesson takes one request from local construction to a verified WebP file. It starts with the API's cost-only dry
run, then performs live generation only when you add `--live`.

## Before you start

You need Python 3.12 or newer and an internet connection. The live step uses the shared AI Horde queue, so completion
time depends on available workers. Anonymous requests do not require an account, but they receive lower priority than
requests made with a registered API key.

Create a virtual environment and install the SDK:

```console
python -m venv .venv
.venv\Scripts\activate
python -m pip install horde-sdk
```

On macOS or Linux, activate with `source .venv/bin/activate`.

## Inspect the request

The example builds one 512 by 512 request. The `dry_run` field is the only difference between estimation and live
submission.

```python
--8 < --"examples/docs/first_image.py:first-image"
```

The simple client owns polling and best-effort cleanup. The request model validates its shape before the first network
call. See the [request and response contracts](../reference/request-response-contracts.md) for that boundary.

## Estimate the cost

Run the example without flags:

```console
python examples/docs/first_image.py
```

The response contains an estimate and creates no generation job:

```text
Estimated cost: 2 kudos
```

The numeric value varies with Horde pricing and request parameters. A line beginning with `Estimated cost:` confirms
that request construction, validation, and the dry-run API call succeeded.

## Generate and verify the file

Opt in to the live request and choose the output path:

```console
python examples/docs/first_image.py --live --output first-image.webp
```

The command first prints the current estimate. It then waits for the shared queue, downloads the first result, saves
it, and asks Pillow to verify the encoded file:

```text
Estimated cost: 2 kudos
Verified image: C:\path\to\first-image.webp
```

Open `first-image.webp`. You now have a complete result and no request ID to manage manually. The
[image generation how-to](../how-to/generate-images.md) shows registered keys, callbacks, timeouts, and multiple
results; the [client layers explanation](../explanation/client-layers.md) shows what the simple client handled for you.
