# 0004: Add a model predictive controller

- Status: accepted
- Date: 2026-11-16

## Context

Decision 0003 left MPC for later. The look-ahead heuristic follows fixed rules (preheat 4 hours ahead, add 1 °C when cheap), and its settings were tuned on the scenarios it is reported on. MPC replaces the rules with a model of the house and an optimizer, so preheating and heat storage follow from the forecast instead of from hand-picked numbers.

## Decision

- **Thermal model:** one room, four numbers fitted with least squares. Each hour the temperature changes by `loss * (outdoor - room) + heat * power + solar * sunshine + drift`. Power is the heat pump's electric power, so the optimizer prices it directly. Extra delay terms for the slow floor were tried and barely helped, so the simplest model was kept.
- **Training data from an identification experiment**, not from the phase 2 runs. In those runs a thermostat raised power exactly when the room cooled, so a model fitted on them was worse than assuming the temperature stays put. `control/identify.py` drives the heat pump directly with a random signal for two weeks from day 45 (training) and two weeks from day 330 (checking).
- **Optimizer:** a linear program solved every hour with SciPy's HiGHS. It chooses 24 hours of power between 0 and 4.5 kW to minimise cost plus 10 EUR per kelvin-hour outside the comfort band (0.2 °C margin). Slack variables keep it solvable when comfort is out of reach.
- **Same interface as the other controllers.** The first hour of the plan becomes a setpoint: the comfort floor when the plan says off, otherwise the temperature the plan expects at the end of the hour, and at least the floor when it heats flat out.
- **Two unseen test periods** were added to the experiment for all controllers: two weeks from day 64 and two weeks from day 300. Nothing was designed or tuned on them.

## Alternatives tried

- **Always ask for the planned temperature.** The first version did this. On sunny days the room ran warmer than the model expected, the setpoint followed it upward, and the thermostat kept heating an empty room at 28 to 30 °C (48 Kh of discomfort in the typical period). Asking for the floor whenever the plan says off fixed it. This change was made after seeing the reported scenarios, which is why the unseen periods were added.

## Result

On the two unseen periods MPC cost 13.7% to 20.2% less than the baseline and 3.3% to 8.3% less than the look-ahead heuristic, with similar discomfort. Full numbers are in [docs/results/phase2.md](../results/phase2.md#mpc).

## Consequences

- The model treats heat as arriving within the hour. In this house it arrives through a heavy floor, so reheating before people return can start late.
- The setpoint mapping means the thermostat, not the optimizer, decides the exact power. Sending the plan's power straight to the heat pump (`oveHeaPumY_u`) would follow the plan more closely, but needs the interface to return more than a setpoint.
- The model is linear and fitted on one house in one simulator. It must be refitted for any other building.
- `scipy` is now a direct dependency.
