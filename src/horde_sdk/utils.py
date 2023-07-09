import random


def seed_to_int(self, s=None):
    if type(s) is int:
        return s
    if s is None or s == "":
        # return a random int
        return random.randint(0, (2**32) - 1)
    n = abs(int(s) if s.isdigit() else int.from_bytes(s.encode(), "little"))
    while n >= 2**32:
        n = n >> 32
        # logger.debug(f"Seed {s} is too large, using {n} instead")
    return n
