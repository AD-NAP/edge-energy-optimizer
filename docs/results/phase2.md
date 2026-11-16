# Phase 2 results: predictive heating control

## Headline

**The predictive controller cut heating cost by 10% to 16% in every scenario tested, with comfort no worse than the baseline.**

**A model predictive controller (MPC), added later, cut cost by 14% to 20% against the baseline on two periods neither controller was built on, 3% to 8% more than the predictive controller.** See [MPC](#mpc) below.

## What was tested

A simulated 192 m² family home in Brussels, heated by a heat pump and underfloor heating. The home is empty on weekdays from 07:00 to 20:00. The simulator is [BOPTEST](https://ibpsa.github.io/project1-boptest/) (test case `bestest_hydronic_heat_pump`, version 0.9.0), which scores every controller the same way.

| | Baseline | Predictive |
| --- | --- | --- |
| Strategy | Thermostat fixed at 21.2 °C all day | Looks 24 hours ahead at occupancy, price, and weather |
| When the home is empty | Keeps heating | Lets the temperature drift down |
| Before people return | Nothing to do | Starts reheating 4 hours ahead |
| When electricity is cheap | Ignores price | Stores 1 °C of extra heat in the floor, except on mild days |

Each controller ran for two weeks in four scenarios: the coldest period of the year and a typical spring period, each under a day/night tariff and under hourly spot prices.

## Results

| Scenario | Cost, baseline | Cost, predictive | Cost saved | Energy saved | Discomfort, baseline | Discomfort, predictive |
| --- | --- | --- | --- | --- | --- | --- |
| Coldest period, day/night tariff | 174.16 EUR | 152.23 EUR | **12.6%** | 12.0% | 1.49 Kh | 1.53 Kh |
| Coldest period, spot prices | 179.56 EUR | 153.83 EUR | **14.3%** | 12.9% | 1.49 Kh | 0.84 Kh |
| Typical period, day/night tariff | 92.49 EUR | 82.95 EUR | **10.3%** | 9.6% | 7.08 Kh | 6.70 Kh |
| Typical period, spot prices | 85.81 EUR | 72.44 EUR | **15.6%** | 14.1% | 7.08 Kh | 6.71 Kh |

Discomfort is measured in kelvin-hours (Kh): how far the temperature was outside the comfort band, multiplied by how long. Lower is better, and 1.5 Kh over two weeks is about a tenth of a degree for 15 hours.

![Cost, energy, and discomfort for both controllers in all four scenarios](../img/phase2_kpis.png)

## How it saves money

The predictive controller stops heating while the home is empty and catches up before people return. The temperature stays inside the comfort band (grey) whenever someone is home.

![Zone temperature against the comfort band in the coldest period](../img/phase2_temperature_peak_heat_day.png)

Under spot prices it also buys more of its heat in the cheaper hours.

![Heating power and electricity price in the coldest period](../img/phase2_power_peak_heat_day.png)

Where the saving comes from, under spot prices:

| | Coldest period | Typical period |
| --- | --- | --- |
| Not heating an empty home | 12.7% | 10.2% |
| Buying heat in cheap hours | 1.6% more | 5.4% more |
| Total | 14.3% | 15.6% |

## What to keep in mind

- **Most of the saving is from not heating an empty home.** Price awareness adds 2 to 5 points. About 0.20 EUR of every kWh is fixed taxes and network fees, so the price a home pays moves far less than the wholesale price underneath it.
- **The price rule does nothing under the day/night tariff.** It looks for the cheapest quarter of the day, and the night rate covers more than a quarter, so no hour stands out. A variant that reacts to any below-average price was tried. It helped under the day/night tariff and hurt under spot prices, for the same total cost, so it was not adopted.
- **Peak power is higher**: 3.9 kW against 3.1 kW in the coldest period, because reheating runs the heat pump hard. This tariff has no peak charge. Where one applies, it would eat into the saving. Phase 4 addresses peaks.
- **The baseline is not perfectly comfortable either.** Its discomfort in the typical period is almost all overheating on sunny days, which no heating controller can prevent in a home with no cooling.
- **The settings were tuned on these same scenarios.** The 10 °C mild-day threshold was chosen after seeing the first results. Expect somewhat smaller savings on weeks the controller has not seen.
- **Forecasts were perfect.** BOPTEST supplied exact weather, prices, and occupancy. Real forecasts are less accurate.
- **One simulated home.** A home that is occupied all day would save much less, because there would be no empty hours to exploit.

## MPC

Added on 16 November 2026 ([decision 0004](../decisions/0004-mpc-controller.md)). Instead of fixed rules, it plans 24 hours of heat pump power every hour, using a fitted model of the house, then hands the first hour to the thermostat as a setpoint.

### The house model

Four numbers, fitted on two weeks where the heat pump followed a random signal (from day 45). The phase 2 runs could not be used: the thermostat raised power exactly when the room cooled, and a model fitted on them was worse than guessing that the temperature stays put.

| Predicting the next 24 hours, two unseen weeks (from day 330) | Mean error |
| --- | --- |
| Temperature stays where it is | 1.08 °C |
| **Fitted model** | **0.50 °C** |

The house loses heat slowly: its time constant is about 49 hours.

### Results

Cost, with discomfort in brackets. The first four rows are the scenarios above. The last four are two-week periods that no controller was designed or tuned on.

| Scenario | Baseline | Predictive | MPC | MPC saved vs baseline | MPC saved vs predictive |
| --- | --- | --- | --- | --- | --- |
| Coldest period, day/night tariff | 174.16 EUR (1.49 Kh) | 152.23 EUR (1.53 Kh) | 148.59 EUR (3.11 Kh) | 14.7% | 2.4% |
| Coldest period, spot prices | 179.56 EUR (1.49 Kh) | 153.83 EUR (0.84 Kh) | 154.36 EUR (1.59 Kh) | 14.0% | -0.3% |
| Typical period, day/night tariff | 92.49 EUR (7.08 Kh) | 82.95 EUR (6.70 Kh) | 78.22 EUR (6.17 Kh) | 15.4% | 5.7% |
| Typical period, spot prices | 85.81 EUR (7.08 Kh) | 72.44 EUR (6.71 Kh) | 71.34 EUR (5.93 Kh) | 16.9% | 1.5% |
| **Unseen, from day 64, day/night tariff** | 132.04 EUR (2.76 Kh) | 113.10 EUR (2.66 Kh) | 107.17 EUR (2.68 Kh) | **18.8%** | **5.2%** |
| **Unseen, from day 64, spot prices** | 123.19 EUR (2.76 Kh) | 101.68 EUR (2.72 Kh) | 98.31 EUR (2.93 Kh) | **20.2%** | **3.3%** |
| **Unseen, from day 300, day/night tariff** | 104.79 EUR (0.21 Kh) | 96.33 EUR (0.03 Kh) | 88.34 EUR (0.08 Kh) | **15.7%** | **8.3%** |
| **Unseen, from day 300, spot prices** | 99.37 EUR (0.21 Kh) | 91.18 EUR (0.05 Kh) | 85.74 EUR (0.06 Kh) | **13.7%** | **6.0%** |

On the unseen periods the predictive controller saves 8% to 18%, a little less than on the weeks it was tuned on, as expected.

### What to keep in mind

- **Reheating starts a little late in the coldest period.** The model treats heat as arriving within the hour, but here it arrives through a heavy floor. Discomfort there is 3.11 Kh against 1.53 Kh, still under a quarter of a degree over two weeks.
- **One design change was made after seeing the reported scenarios.** The first version asked the thermostat for the temperature the plan expected, even when the plan said "off". On sunny days the room ran warmer than the model predicted, the setpoint followed it up, and the thermostat heated an empty room to 30 °C (48 Kh). It now asks for the comfort floor whenever the plan says off. The unseen periods were added because of this change.
- **The thermostat, not the optimizer, sets the exact power.** Driving the heat pump directly would follow the plan more closely.
- **Peak power** is 3.3 to 3.8 kW, between the baseline and the predictive controller.

## Reproduce

Start BOPTEST as described in the [README](../../README.md), then:

```bash
uv run python -m edge_energy_optimizer.control.identify
uv run python -m edge_energy_optimizer.control.thermal_model
uv run python -m edge_energy_optimizer.control.experiment
uv run python -m edge_energy_optimizer.control.report
```

The numbers above are in [phase2_kpis.csv](phase2_kpis.csv).
