"""The predictive controller: a look-ahead heuristic over the forecast.

Three rules, applied in order:
1. Sit just above the lower comfort bound, which sets back by itself when the house is empty.
2. Preheat: use the highest lower bound of the next `preheat_hours`, so the house is warm on arrival.
3. Store heat: add `boost_c` when the price now is among the cheapest of the forecast.
The result never goes above the upper comfort bound.
"""

import numpy as np

from edge_energy_optimizer.control.base import Forecast, Observation


class PredictiveController:
    def __init__(
        self,
        margin_c: float = 0.2,
        preheat_hours: int = 4,
        boost_c: float = 1.0,
        cheap_quantile: float = 0.25,
    ) -> None:
        self._margin_c = margin_c
        self._preheat_hours = preheat_hours
        self._boost_c = boost_c
        self._cheap_quantile = cheap_quantile

    def setpoint_c(self, observation: Observation, forecast: Forecast) -> float:
        # Index 0 is now, so the window is now plus the next `preheat_hours`.
        window = slice(0, self._preheat_hours + 1)
        setpoint = max(forecast.lower_c[window]) + self._margin_c

        # Strictly below, so a flat price is never "cheap".
        if forecast.price[0] < np.quantile(forecast.price, self._cheap_quantile):
            setpoint += self._boost_c

        ceiling = min(forecast.upper_c[window]) - self._margin_c
        return round(float(min(setpoint, ceiling)), 2)
