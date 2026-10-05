"""The baseline: a thermostat that holds one setpoint all the time."""

from edge_energy_optimizer.control.base import Forecast, Observation

# The occupied lower comfort bound (21) plus the 0.2 margin BOPTEST's own baseline uses.
DEFAULT_SETPOINT_C = 21.2


class FixedSetpointController:
    def __init__(self, setpoint_c: float = DEFAULT_SETPOINT_C) -> None:
        self._setpoint_c = setpoint_c

    def setpoint_c(self, observation: Observation, forecast: Forecast) -> float:
        return self._setpoint_c
