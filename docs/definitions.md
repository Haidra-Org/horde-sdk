# horde_sdk specific definitions

See also the [naming section of the style guide](concepts/style_guide.md#naming-conventions) for additional explanations of certain terms.

## API

### Clients

#### ManualClient

A manual client interacts with an API but does not provide any context management. Clients of this kind do not automatically cancel in-process jobs, for example.

#### ClientSession

Client session classes provide context management for API operations. They automatically cancel or follow-up on any in-process operations when exiting the context. Client sessions generally inherit from ManualClient.

## Jobs/Generations/Inference

### Generation

A generation is a single instance of inference or generation. Generations can result in one or more logical outputs. For example, a text generation may result in a single string output, while an image generation may result in one or multiple images being returned. Generations may be a single step in a multi-step process. Not to be confused with a job.

### Job

A job is a collection of one or more generations that are executed together. Jobs can be thought of as a batch of generations that are processed in parallel or sequentially, depending on the API and client implementation. A job may consist of multiple generations that share common parameters or context. Jobs also contain metadata from the dispatch source, such as the job ID, generation IDs, whether the job is subject to NSFW checks, etc. Not to be confused with a generation.

### "batch", "batch_size", "n_iter", "number_expected_results", etc

These terms refer to the number of results that are expected to be returned from a generation during a *single run of inference*. In the case of image generation, the user may request multiple images which share all parameters and are generated at the same time. If the user requests 4 images using 25 steps, only 25 steps of inference run. Contrast this with a job that may consist of multiple generations, each with their own parameters and context, which run in parallel or sequentially each with their own inference steps.
