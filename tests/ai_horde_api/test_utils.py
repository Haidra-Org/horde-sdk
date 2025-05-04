from horde_sdk.utils import seed_to_int


class TestSeedToInt:

    def test_convert_integer_seed_to_integer(self) -> None:
        """Test converting an integer seed to an integer."""
        seed = 12345
        result = seed_to_int(seed)
        assert result == seed, f"Expected {seed}, got {result}"

    def test_handle_non_digit_string_seed(self) -> None:
        """Handle non-digit string seed."""
        seed = "abc"
        result = seed_to_int(seed)
        expected = abs(int.from_bytes(seed.encode(), "little")) % (2**32)
        assert result == expected, f"Expected {expected}, got {result}"

    def test_return_random_integer_when_seed_is_none(self) -> None:
        """Return random integer when seed is None."""
        result = seed_to_int(None)
        assert isinstance(result, int), f"Expected an integer, got {type(result)}"

    def test_random_integer_for_empty_string_seed(self) -> None:
        """Return random integer when seed is an empty string."""
        result = seed_to_int("")
        assert isinstance(result, int), f"Expected an integer, got {type(result)}"

    def test_negative_integer_seed(self) -> None:
        """Handle negative integer seed."""
        seed = -12345
        result = seed_to_int(seed)
        assert result == seed, f"Expected {seed}, got {result}"

    def test_consistent_output_for_same_string_seed(self) -> None:
        """Ensure consistent output for same string seed."""
        seed = "test_seed"
        result1 = seed_to_int(seed)
        result2 = seed_to_int(seed)
        assert result1 == result2, f"Expected consistent output, got {result1} and {result2}"

    def test_maximum_integer_seed(self) -> None:
        """Test with maximum integer value."""
        max_int = (2**32) - 1
        result = seed_to_int(max_int)
        assert result == max_int, f"Expected {max_int}, got {result}"

    def test_arbitrary_string_seed(self) -> None:
        """Test with an arbitrary string seed."""
        seed = "test_seed"
        result = seed_to_int(seed)
        assert isinstance(result, int), f"Expected an integer, got {type(result)}"
        assert result == 1953719668, f"Expected 1953719668, got {result}"
