"""The controller interface. Every control strategy plugs in through `Controller`.

A controller sees one observation and one forecast, and answers with a zone
temperature setpoint. It knows nothing about BOPTEST or any protocol.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Observation:
    """What the building looks like right now."""

    time_s: float
    zone_temp_c: float


@dataclass(frozen=True)
class Forecast:
    """What is expected from now on. All lists line up with `time_s`, and index 0 is now."""

    time_s: list[float]
    lower_c: list[float]
    upper_c: list[float]
    price: list[float]
    outdoor_c: list[float]


@runtime_checkable
class Controller(Protocol):
    def setpoint_c(self, observation: Observation, forecast: Forecast) -> float:
        """Return the zone temperature setpoint in degrees Celsius for the next step."""
        ...
