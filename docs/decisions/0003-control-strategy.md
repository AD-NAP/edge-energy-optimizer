# 0003: Control strategy and test building

- Status: accepted
- Date: 2026-10-05

## Context

Phase 2 needs a building to control, a baseline to beat, and a control strategy. The open questions from phase 1 were which BOPTEST test case to use, and rule-based control versus model predictive control (MPC). Phases 1 and 2 are due on 11 October 2026.

## Decision

- **Building:** BOPTEST test case `bestest_hydronic_heat_pump`, version 0.9.0, run locally with Docker. It has one zone, one heat pump, and one input that matters (the zone temperature setpoint), so the control problem stays small.
- **Interface:** a controller is any class with `setpoint_c(observation, forecast) -> float`, in degrees Celsius. Controllers know nothing about BOPTEST. The experiment runner translates to and from the BOPTEST API.
- **Baseline:** a thermostat fixed at 21.2 °C. That is the occupied lower comfort bound plus the 0.2 °C margin BOPTEST's built-in controller uses.
- **Strategy:** a look-ahead heuristic, re-decided every hour from a 24-hour forecast. It follows the lower comfort bound, preheats 4 hours before occupancy, and adds 1 °C when the current price is in the cheapest quarter of the forecast, unless the outdoor forecast reaches 10 °C.
- **Not MPC, for now.** MPC needs a thermal model of the building and an optimizer. The heuristic needs neither, is easy to explain, and already saves 10% to 16%.
- **Forecasts:** BOPTEST's own forecasts of weather, price, and comfort bounds. The phase 1 load forecaster is not used, because the controller does not need a load forecast.
- **Evaluation:** both controllers on `peak_heat_day` and `typical_heat_day`, under `dynamic` and `highly_dynamic` prices, compared on BOPTEST's cost, energy, and thermal discomfort KPIs.

## Alternatives tried

- **Boost on any below-average price**, in place of the cheapest quarter. Cost fell under the day/night tariff and rose under spot prices, for the same total (461.10 EUR against 461.45 EUR across the four scenarios). Not adopted.
- **No mild-day rule.** The first version overheated the home on sunny spring days (8.32 Kh against the baseline's 7.08 Kh under spot prices). The rule brought that to 6.71 Kh.

## Consequences

- The heuristic's settings (4 hours, 1 °C, cheapest quarter, 10 °C) were tuned on the scenarios they are reported on. Results on other weeks will be somewhat worse.
- Outdoor temperature stands in for sunshine in the mild-day rule. The solar forecast would be a more direct signal.
- The price rule is inactive under the day/night tariff, where the cheap rate covers more than a quarter of the day.
- Preheating raises peak power from about 3.1 kW to 3.9 kW. That is free under these tariffs and matters for phase 4.
- An MPC controller can be added later as a new class with the same method. Nothing else has to change except the runner's list of controllers.
- BOPTEST 0.9.0 pins MinIO images that were removed from Docker Hub in September 2026. `docker/boptest.override.yml` replaces them with Chainguard's builds. Drop the override when BOPTEST fixes this upstream.
