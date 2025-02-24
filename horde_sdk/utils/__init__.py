import random


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
