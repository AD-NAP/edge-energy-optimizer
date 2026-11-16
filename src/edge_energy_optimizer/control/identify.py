"""Collect training data for the thermal model by driving the heat pump directly.

The saved phase 2 runs are no good for this: a thermostat was in charge, so power always
rose exactly when the room cooled, and a model cannot tell cause from effect. Here the heat
pump follows a random signal instead, on dates outside the reported scenarios.

BOPTEST must be running first (see the README).
Run with: uv run python -m edge_energy_optimizer.control.identify
"""

import numpy as np
import pandas as pd

from edge_energy_optimizer.control.boptest import BoptestClient
from edge_energy_optimizer.control.experiment import KELVIN, POWER_POINTS, SERIES_DIR, STEP_S, TESTCASE

DAY_S = 86400
WARMUP_S = 7 * DAY_S
# Day of the year each run starts on, chosen away from the reported periods (days 16 to 30
# and 108 to 122). One run trains the model, the other checks it on weeks it never saw.
RUNS = {"train": 45, "validate": 330}
RUN_DAYS = 14
LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]
POINTS = ["reaTZon_y", "weaSta_reaWeaTDryBul_y", "weaSta_reaWeaHGloHor_y"] + POWER_POINTS


def excitation(hours: int, seed: int, max_hold_hours: int = 6) -> list[float]:
    """A random heat pump signal: each level is held for 1 to `max_hold_hours` hours."""
    rng = np.random.default_rng(seed)
    signal: list[float] = []
    while len(signal) < hours:
        # Always move to a new level, so two holds never merge into one long one.
        choices = [level for level in LEVELS if not signal or level != signal[-1]]
        signal += [float(rng.choice(choices))] * int(rng.integers(1, max_hold_hours + 1))
    return signal[:hours]


def run_identification(client, start_day: int, signal: list[float]) -> pd.DataFrame:
    """Play `signal` into the heat pump one hour at a time. Returns hourly data."""
    client.select(TESTCASE)
    try:
        start_s = client.initialize(start_day * DAY_S, WARMUP_S)["time"]
        time_s = start_s
        for u in signal:
            time_s = client.advance({"oveHeaPumY_u": u, "oveHeaPumY_activate": 1})["time"]
        measured = client.results(POINTS, start_s, time_s)
    finally:
        client.stop()
    return to_hourly(measured, start_s, len(signal))


def to_hourly(measured: dict, start_s: float, hours: int) -> pd.DataFrame:
    """One row per control hour. The temperature is taken at the end of the hour,
    everything else is averaged over it, so row k reads "this hour's inputs led to this"."""
    raw = pd.DataFrame(measured).set_index("time")
    starts = start_s + STEP_S * np.arange(hours)
    inside = raw.index < start_s + hours * STEP_S
    hour = ((raw.index[inside] - start_s) // STEP_S).astype(int)
    averages = pd.DataFrame({
        "power_kw": raw.loc[inside, POWER_POINTS].sum(axis=1) / 1000,
        "outdoor_c": raw.loc[inside, "weaSta_reaWeaTDryBul_y"] - KELVIN,
        "solar_w_m2": raw.loc[inside, "weaSta_reaWeaHGloHor_y"],
    }).groupby(hour).mean()
    # The last sample at or before the end of each hour.
    zone = raw["reaTZon_y"].reindex(starts + STEP_S, method="ffill").to_numpy() - KELVIN
    data = averages.set_index(pd.Index(starts, name="time_s"))
    data.insert(0, "zone_temp_c", zone)
    return data


def main() -> None:
    SERIES_DIR.mkdir(parents=True, exist_ok=True)
    client = BoptestClient()
    for seed, (name, start_day) in enumerate(RUNS.items()):
        print(f"Identification run '{name}' from day {start_day}...")
        data = run_identification(client, start_day, excitation(RUN_DAYS * 24, seed=seed))
        data.to_csv(SERIES_DIR / f"identification_{name}.csv")
        print(data.describe().round(2).to_string())


if __name__ == "__main__":
    main()
