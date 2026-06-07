"""Stimulus schedules and experimental condition definitions."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class StimulusSchedule:
    """Discrete-time flash and beep event schedule."""

    flash_times: frozenset[int]
    beep_times: frozenset[int]

    def is_flash(self, t: int) -> bool:
        """Return True if a flash occurs at timestep t."""
        return t in self.flash_times

    def is_beep(self, t: int) -> bool:
        """Return True if a beep occurs at timestep t."""
        return t in self.beep_times


class Condition(Enum):
    """Experimental conditions for the flash-beep illusion."""

    A = "A"
    B = "B"
    C = "C"


_CONDITION_SCHEDULES = {
    Condition.A: StimulusSchedule(flash_times=frozenset({5}), beep_times=frozenset({5, 10})),
    Condition.B: StimulusSchedule(flash_times=frozenset({5}), beep_times=frozenset({5})),
    Condition.C: StimulusSchedule(flash_times=frozenset({5}), beep_times=frozenset()),
}


def get_condition(name: str) -> StimulusSchedule:
    """
    Return the stimulus schedule for a named experimental condition.

    Args:
        name: Condition identifier ('A', 'B', or 'C').

    Returns:
        StimulusSchedule for the requested condition.

    Raises:
        ValueError: If name is not a valid condition identifier.
    """
    key = Condition(name.upper())
    return _CONDITION_SCHEDULES[key]
