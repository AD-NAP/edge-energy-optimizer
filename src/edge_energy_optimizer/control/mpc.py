"""Model predictive control: plan 24 hours of heating, apply the first hour, re-plan next hour.

Every hour the controller solves a small linear program:

    choose   power[0..23] in kW, between 0 and the heat pump's maximum
    minimise the electricity cost, plus a penalty for every kelvin-hour outside comfort
    where    the room temperature follows the fitted thermal model

The plan is a list of power levels, but the runner speaks in setpoints. So the first hour of
the plan becomes a setpoint: the comfort floor when the plan says off, otherwise the temperature
the plan expects at the end of the hour. When the plan heats flat out, it asks for at least the
floor, so the thermostat heats flat out too.

The numeric settings below were fixed before any run and never tuned. The rule for the "off"
setpoint was added after the first run on the reported scenarios (decision 0004), so the
experiment also scores every controller on two unseen periods.
"""

import numpy as np
from scipy.optimize import linprog

from edge_energy_optimizer.control.base import Forecast, Observation
from edge_energy_optimizer.control.thermal_model import ThermalModel, load

# Planned power below this counts as off.
OFF_KW = 0.05


class MPCController:
    def __init__(
        self,
        model: ThermalModel | None = None,
        max_power_kw: float = 4.5,
        margin_c: float = 0.2,
        discomfort_eur_per_kh: float = 10.0,
    ) -> None:
        # Loaded on first use, so importing the runner does not need a fitted model on disk.
        self._model = model
        self._max_power_kw = max_power_kw
        self._margin_c = margin_c
        self._discomfort_eur_per_kh = discomfort_eur_per_kh

    def setpoint_c(self, observation: Observation, forecast: Forecast) -> float:
        power, temps = self.plan(observation, forecast)
        floor = forecast.lower_c[1] + self._margin_c
        ceiling = forecast.upper_c[1] - self._margin_c
        if power[0] < OFF_KW:
            # Off: ask for the floor. Asking for the expected temperature instead would make the
            # thermostat chase the room upward whenever it runs warmer than the model thinks.
            setpoint = floor
        elif power[0] >= 0.95 * self._max_power_kw:
            setpoint = max(temps[0], floor)
        else:
            setpoint = temps[0]
        return round(float(np.clip(setpoint, floor, ceiling)), 2)

    def plan(self, observation: Observation, forecast: Forecast) -> tuple[np.ndarray, np.ndarray]:
        """The cheapest heating plan for the forecast. Returns power per hour and the
        temperature the model expects at the end of each hour."""
        if self._model is None:
            self._model = load()
        # Forecast index 0 is now. Hour k runs from point k to point k+1, so the inputs of
        # hour k come from point k, and its end-of-hour comfort band from point k+1.
        hours = len(forecast.time_s) - 1
        price = np.array(forecast.price[:hours])
        solar = forecast.solar_w_m2[:hours] if forecast.solar_w_m2 else [0.0] * hours
        free, gain = self._model.response(observation.zone_temp_c, forecast.outdoor_c[:hours], solar)
        lower = np.array(forecast.lower_c[1:]) + self._margin_c
        upper = np.array(forecast.upper_c[1:]) - self._margin_c

        # Variables: power (hours), too cold (hours), too warm (hours). Slack keeps the problem
        # solvable when comfort is out of reach, such as a freezing room with people home.
        eye, zero = np.eye(hours), np.zeros((hours, hours))
        cost = np.concatenate([price, np.full(2 * hours, self._discomfort_eur_per_kh)])
        # free + gain @ power + too_cold >= lower   ->   -gain @ power - too_cold <= free - lower
        # free + gain @ power - too_warm <= upper   ->    gain @ power - too_warm <= upper - free
        a_ub = np.block([[-gain, -eye, zero], [gain, zero, -eye]])
        b_ub = np.concatenate([free - lower, upper - free])
        bounds = [(0, self._max_power_kw)] * hours + [(0, None)] * (2 * hours)

        result = linprog(cost, A_ub=a_ub, b_ub=b_ub, bounds=bounds, method="highs")
        if not result.success:
            raise RuntimeError(f"MPC could not solve its plan: {result.message}")
        power = result.x[:hours]
        return power, free + gain @ power
