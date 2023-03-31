from setuptools import setup  # noqa: D100

setup(
    package_data={
        "horde_shared_models": [
            "py.typed",
            "*.pyi",
            "ai_horde_api/*.pyi",
            "generic_api/*.pyi",
            "ratings_api/*.pyi",
        ]
    }
)
