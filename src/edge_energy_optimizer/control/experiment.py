"""Run every controller on every scenario against BOPTEST and save the results.

BOPTEST must be running first (see the README).
Run with: uv run python -m edge_energy_optimizer.control.experiment
"""

from pathlib import Path

import pandas as pd

from edge_energy_optimizer.control.base import Controller, Forecast, Observation
from edge_energy_optimizer.control.baseline import FixedSetpointController
from edge_energy_optimizer.control.boptest import BoptestClient
from edge_energy_optimizer.control.mpc import MPCController
from edge_energy_optimizer.control.predictive import PredictiveController

TESTCASE = "bestest_hydronic_heat_pump"
FLOOR_AREA_M2 = 192.0
TIME_PERIODS = ["peak_heat_day", "typical_heat_day"]
# Two-week periods no controller was designed or tuned on, given by their first day of the
# year. Days 45 to 59 and 330 to 344 are taken by the thermal model's identification runs.
UNSEEN_PERIODS = {"unseen_march": 64, "unseen_october": 300}
WARMUP_S = 7 * 86400
PRICE_POINTS = {
    "dynamic": "PriceElectricPowerDynamic",
    "highly_dynamic": "PriceElectricPowerHighlyDynamic",
}
CONTROLLERS: dict[str, Controller] = {
    "baseline": FixedSetpointController(),
    "predictive": PredictiveController(),
    "mpc": MPCController(),
}

STEP_S = 3600
HORIZON_S = 24 * STEP_S
# Each BOPTEST time period is two weeks long.
EPISODE_STEPS = 14 * 24
POWER_POINTS = ["reaPHeaPum_y", "reaPPumEmi_y", "reaPFan_y"]

KELVIN = 273.15
KPI_PATH = Path("docs/results/phase2_kpis.csv")
SERIES_DIR = Path("data/phase2")


def to_forecast(payload: dict, electricity_price: str) -> Forecast:
    """Turn a BOPTEST forecast payload into the controller's `Forecast`."""
    return Forecast(
        time_s=payload["time"],
        lower_c=[k - KELVIN for k in payload["LowerSetp[1]"]],
        upper_c=[k - KELVIN for k in payload["UpperSetp[1]"]],
        price=payload[PRICE_POINTS[electricity_price]],
        outdoor_c=[k - KELVIN for k in payload["TDryBul"]],
        solar_w_m2=payload.get("HGloHor", []),
    )


def to_inputs(setpoint_c: float) -> dict:
    """Turn a setpoint into the BOPTEST inputs that override the zone thermostat."""
    return {"oveTSet_u": round(setpoint_c + KELVIN, 2), "oveTSet_activate": 1}


def run_episode(
    client,
    controller: Controller,
    time_period: str,
    electricity_price: str,
    steps: int = EPISODE_STEPS,
    start_day: int | None = None,
) -> tuple[dict, pd.DataFrame]:
    """Run one controller through one scenario. Returns the KPIs and a 15-minute time series.

    With `start_day`, the run starts on that day of the year instead of at `time_period`,
    which is then only a label."""
    forecast_points = [
        "TDryBul", "HGloHor", "LowerSetp[1]", "UpperSetp[1]", PRICE_POINTS[electricity_price]
    ]
    client.select(TESTCASE)
    try:
        if start_day is None:
            measurements = client.set_scenario(time_period, electricity_price)
        else:
            client.set_price(electricity_price)
            measurements = client.initialize(start_day * 86400, WARMUP_S)
        start_s = measurements["time"]
        decisions = []
        for _ in range(steps):
            forecast = to_forecast(
                client.forecast(forecast_points, HORIZON_S, STEP_S), electricity_price
            )
            observation = Observation(measurements["time"], measurements["reaTZon_y"] - KELVIN)
            setpoint = controller.setpoint_c(observation, forecast)
            decisions.append({
                "time_s": observation.time_s,
                "setpoint_c": setpoint,
                "lower_c": forecast.lower_c[0],
                "upper_c": forecast.upper_c[0],
                "price": forecast.price[0],
                "outdoor_c": forecast.outdoor_c[0],
            })
            measurements = client.advance(to_inputs(setpoint))

        kpis = client.kpis()
        measured = client.results(["reaTZon_y"] + POWER_POINTS, start_s, measurements["time"])
    finally:
        client.stop()
    return kpis, _to_series(measured, decisions)


def _to_series(measured: dict, decisions: list[dict]) -> pd.DataFrame:
    """Join what the building did with what the controller decided, on a 15-minute grid."""
    raw = pd.DataFrame(measured)
    raw.index = pd.to_timedelta(raw.pop("time"), unit="s")
    series = pd.DataFrame({
        "zone_temp_c": raw["reaTZon_y"] - KELVIN,
        "power_kw": raw[POWER_POINTS].sum(axis=1) / 1000,
    }).resample("15min").mean()

    decided = pd.DataFrame(decisions)
    decided.index = pd.to_timedelta(decided.pop("time_s"), unit="s")
    # A decision holds until the next one, so carry it forward across the hour.
    series = series.join(decided.reindex(series.index, method="ffill"))
    series.index = series.index.total_seconds().rename("time_s")
    return series


def main() -> None:
    SERIES_DIR.mkdir(parents=True, exist_ok=True)
    KPI_PATH.parent.mkdir(parents=True, exist_ok=True)
    client = BoptestClient()

    rows = []
    periods = {name: None for name in TIME_PERIODS} | UNSEEN_PERIODS
    for time_period, start_day in periods.items():
        for electricity_price in PRICE_POINTS:
            for name, controller in CONTROLLERS.items():
                print(f"Running {name} on {time_period} with {electricity_price} prices...")
                kpis, series = run_episode(
                    client, controller, time_period, electricity_price, start_day=start_day
                )
                series.to_csv(SERIES_DIR / f"{name}_{time_period}_{electricity_price}.csv")
                rows.append({
                    "time_period": time_period,
                    "electricity_price": electricity_price,
                    "controller": name,
                    # BOPTEST reports energy and cost per square metre of floor.
                    "energy_kwh": kpis["ener_tot"] * FLOOR_AREA_M2,
                    "cost_eur": kpis["cost_tot"] * FLOOR_AREA_M2,
                    "discomfort_kh": kpis["tdis_tot"],
                    "peak_kw": kpis["pele_tot"] * FLOOR_AREA_M2,
                })

    results = pd.DataFrame(rows)
    results.to_csv(KPI_PATH, index=False)
    print(results.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
