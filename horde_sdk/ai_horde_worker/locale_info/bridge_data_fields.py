"""This file contains the descriptions for the fields in the bridge data file.

This is used to generate, among other things, the bridge data config and the webui. The _L function is used to mark
strings for translation.
"""

from horde_sdk.localize import _L

BRIDGE_DATA_FIELD_DESCRIPTIONS = {
    "api_key": _L("The API key to use for this worker. You can get one from https://aihorde.net/worker"),
    "dreamer_name": _L("The name to use when running a dreamer worker."),
    "cache_home": _L(
        (
            "The directory to use to store models. Each model configured to load will take "
            "around 2 gb of space. Some may take up to 7gb."
        ),
    ),
    "temp_dir": _L("The directory to use for temporary files. This should ideally be the fastest drive you have."),
    "allow_unsafe_ip": _L("If set to False, this worker will no longer pick img2img jobs from unsafe IPs."),
    "priority_usernames": _L(
        (
            "The API key used to run this worker always has priority to this worker. "
            "If you want to add more users to this list, add their horde usernames here."
        ),
    ),
    "always_download": _L(
        "Always download models when required without prompting. If disk space is an issue, set this to False.",
    ),
    "suppress_speed_warnings": _L(
        (
            "If you are getting messages about jobs taking too long, you can change this to true if you no "
            "longer want to see them. Please note, that if you *are* getting these messages, you are serving jobs "
            "substantially slower than is ideal, and you very likely would get more kudos/hr if you just lower your "
            "max_power."
        ),
    ),
    "horde_url": _L(
        (
            "You probably don't need to change this unless you are running your own horde, in which "
            "case you can change this to that URL."
        ),
    ),
    "allow_controlnet": _L(
        (
            "If set to True, this worker start picking up ControlNet jobs "
            "ControlNet is really heavy and requires a good GPU and works best if you have at least 12G VRAM. "
            "If you are having memory issues or are running out of CUDA VRAM and crashing, set this to false."
        ),
    ),
    "allow_img2img": _L("If set to False, this worker will no longer pick img2img jobs"),
    "allow_lora": _L(
        (
            "If set to True, this worker start picking up jobs requesting LoRas Your worker will download the top 10Gb"
            " of non-character LoRas and then will ad-hoc download any LoRa requested which you do not have, and cache"
            " that for a number a days"
        ),
    ),
    "max_lora_cache_size": _L(
        (
            "(Gigabytes) Use this setting to control how much extra space LoRas can take after you downloaded the"
            " curated LoRas all workers download. If a new Lora would exceed this space, an old lora you've downloaded"
            " previously will be deleted. Expect at least 5gb of space to be used by the curated LoRas."
        ),
    ),
    "allow_painting": _L(
        (
            "If set to True, this worker will can pick inpainting jobs. "
            "You will have to have inpainting models downloaded for this to work."
        ),
    ),
    "allow_post_processing": _L(
        (
            "If true, you will be able to pick up post-processing jobs, such as ones that perform "
            "face-fixing or upscaling."
        ),
    ),
    "blacklist": _L(
        "A list of words which if they appear in a prompt in a job, you do not want your worker to accept that job.",
    ),
    "censor_nsfw": _L(
        (
            "Set this to True if you want your worker to censor NSFW generations. "
            "This will only be active is horde_nsfw == False"
        ),
    ),
    "censorlist": _L(
        (
            "A list of words for which you always want to allow the NSFW censor filter, "
            "even when this worker is in NSFW mode"
        ),
    ),
    "disable_disk_cache": _L(
        (
            "Disable the disk cache. By default if RAM and VRAM are filled (up to the limits above) then "
            "models will spill over in to a disk cache. If you don't want this to happen you can disable it here.\n"
            "Note that if you disable disk cache and specify more models to load than will fit in memory your worker "
            "will endlessly cycle loading and unloading models."
        ),
    ),
    "dynamic_models": _L(
        (
            "If this is set, your worker will try and load models which have very high queue clear times. This has the"
            " practical effect of making the less commonly offered models have better queue times. However, it will"
            " also mean that your worker will have to download more models. You can control the maximum number of"
            " dynamic models with the config options `max_dynamic_models_to_download`."
        ),
    ),
    "max_dynamic_models_to_download": _L(
        (
            "The maximum number of models to download if dynamic_models is set to True. "
            "Models average around 2gb each but some are as large as 7gb. See `dynamic_models` for more information."
        ),
    ),
    "max_power": _L(
        (
            "This is used to calculate the maximum resolution of an image you can generate. "
            "8 is the default and will allow you to generate 512x512 images.\n"
            "16 will allow you to generate 768x768 images.\n"
            "32 will allow you to generate 1024x1024 images.\n"
            "Please note that `max_power` 8 still allows you to generate images 256x1024, 1024x256, or any other "
            "resolution which works out to less than or equal to 512 * 512 (multiplication)."
        ),
    ),
    "image_models_to_load": _L(
        (
            "The stable diffusions model to load. If you have more models loaded than will fit in memory, the worker"
            " will automatically unload models which have been used the least recently and cache them on disk. It is"
            " generally recommended to load as many models as you can comfortably fit in memory, as this will allow"
            " you to generate images faster (without having to wait on reading from disk).\nHowever, if you are"
            " loading many models, you do get a bonus per model loaded (2 kudos/10 minutes per model),so there is a"
            " break-even point where it is better to load more models and use the disk-cache. Some other valid"
            ' values:\n"ALL MODELS"\n"top 1"\n"top n" # where n is a number\n"ALL SFW MODELS"\n"ALL NSFW MODELS"\nThe'
            " webui can give you an easier way to select models to load."
        ),
    ),
    "image_models_to_skip": _L(
        "A list of models to skip loading. This is useful if you want to load all models except for a certain few.",
    ),
    "nsfw": _L("Set this to false, if you do not want your worker to receive requests for NSFW generations "),
    "number_of_dynamic_models_to_load": _L(
        (
            "The number of dynamic models to load at a time. See `dynamic_models` for more information. "
            "Also note that ram_to_leave_free and vram_to_leave_free are factors as well."
        ),
    ),
    "queue_size": _L(
        (
            "The number of jobs to accept at a time. If you set this to 1, your worker will accept 2 jobs at "
            "a time, 1 to work on, and 1 to have ready to go when it finishes the first job. Unless you have specific "
            "reasons which you understand well, you should leave this at 1."
        ),
    ),
    "threads": _L(
        (
            "The number of concurrent jobs to run. Generally, if you raise this value, you will need to have "
            "`max_power` lower than your highest achievable `max_power` that you can run with 1 thread."
        ),
    ),
    "require_upfront_kudos": _L(
        "If true, anonymous users or users with no kudos will not be able to submit jobs to your worker.",
    ),
    "ram_to_leave_free": _L(
        (
            "The amount of total system ram to try and leave free. You should try and leave at least 8gb "
            "free. If you are doing other things on your computer, you should leave more free."
        ),
    ),
    "vram_to_leave_free": _L(
        (
            "The amount of vram to leave free. You shouldn't change this value unless you fully understand "
            "the consequences. Lowering this value even a little can cause your worker to crash."
        ),
    ),
    "insert_test": _L("test"),
    "alchemist_name": _L("The name to use when running an alchemist worker. Will default to `worker_name` if not set"),
    "forms": _L(
        (
            "The type of services the alchemist worker will provide. "
            "Caption: Generate a caption for an image\n"
            "NSFW: Make a guess if an image is NSFW or not\n"
            "Interrogation: Returns the clip tags for an image\n"
            "Post-Process: Apply post-processing to an image, such as upscaling or face-fixing"
        ),
    ),
    "kai_url": _L("The URL of the KoboldAI Client API. This is only used if you are running a scribe worker."),
    "max_context_length": _L("The max tokens to use from the prompt"),
    "max_length": _L("The max amount of tokens to generate with this worker"),
    "branded_model": _L(
        (
            "When set to true, the horde alias behind the API key will be appended to the model that is advertised to"
            " the horde. This will prevent the model from being used from the shared pool, but will ensure that no"
            " other worker can pretend to serve it"
        ),
    ),
    "extra_stable_diffusion_models_folders": _L(
        (
            "A list of folders to search for stable diffusion models. "
            "This is useful if you want to load models from a folder other than the default "
            "or if you want to load models from multiple folders."
        ),
    ),
    "test": _L("If set to true, the worker will not actually accept jobs, but will instead just print them out."),
}
