"""Contains utility functions and classes for the Horde SDK."""

import random

import horde_sdk
import horde_sdk._version
from horde_sdk.consts import horde_sdk_github_url


def seed_to_int(s: int | str | None = None) -> int:
    """Convert a seed to an int. If s is None or an empty string, a random int is returned."""
    if isinstance(s, int):
        return s

    if s is None or s == "":
        # return a random int
        return random.randint(0, (2**32) - 1)

    # Convert the seed to an int
    n = abs(int(s) if s.isdigit() else int.from_bytes(s.encode(), "little"))

    # Ensure the int is within the range of a 32-bit unsigned int
    return n % (2**32) if n > (2**32) - 1 else n


def create_bridge_agent_string(client_name: str, client_version: str, client_contact_or_url: str) -> str:
    """Create a bridge agent string.

    Args:
        client_name (str): The name of the client.
        client_version (str): The version of the client.
        client_contact_or_url (str): The contact information or URL for the client.

    Returns:
        str: The formatted bridge agent string.
    """
    return f"{client_name}:{client_version}:{client_contact_or_url}"


default_bridge_agent_string = create_bridge_agent_string(
    client_name=horde_sdk.__name__,
    client_version=horde_sdk._version.__version__,
    client_contact_or_url=horde_sdk_github_url,
)
