"""Contains the definitions and functions for dealing with kudos."""


class KudosInfo:
    """Defines how kudos are calculated."""

    uptime_reward_per_tick = 50
    uptime_frequency_per_hour = 6
    uptime_frequency_per_day = uptime_frequency_per_hour * 24
    per_model_bonus_per_tick = 2

    def get_uptime_reward_per_tick(self, number_of_models: int | None = None) -> int:
        """Return the amount of kudos earned per tick.

        Args:
            number_of_models (int | None, optional): Defaults to None.

        Returns:
            int: The amount of kudos earned per tick.
        """
        if number_of_models is None:
            return self.uptime_reward_per_tick

        return int(self.uptime_reward_per_tick + number_of_models * self.per_model_bonus_per_tick)

    def get_uptime_reward_per_hour(self, number_of_models: int | None = None) -> int:
        """Return the amount of kudos earned per hour.

        Args:
            number_of_models (int | None, optional): Defaults to None.

        Returns:
            int: The amount of kudos earned per hour.
        """
        return int(self.get_uptime_reward_per_tick(number_of_models) * self.uptime_frequency_per_hour)
