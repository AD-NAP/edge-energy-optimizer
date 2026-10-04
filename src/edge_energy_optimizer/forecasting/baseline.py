"""Naive forecasts: the bar any real model has to clear.

Run with: uv run python -m edge_energy_optimizer.forecasting.baseline
"""

import pandas as pd

from edge_energy_optimizer.forecasting.dataset import build_dataset

# Name -> how many hours back the forecast copies from.
BASELINES = {
    "same hour yesterday": 24,
    "same hour last week": 168,
}


def naive_forecast(load: pd.Series, lag_hours: int) -> pd.Series:
    """Predict each hour as the load observed `lag_hours` earlier."""
    return load.shift(lag_hours)


def main() -> None:
    load = build_dataset()["load_kwh"]
    # Skip the first week so both baselines are scored on the same hours.
    scored = load.iloc[max(BASELINES.values()):]

    print(f"Average load: {scored.mean():.1f} kWh per hour")
    for name, lag_hours in BASELINES.items():
        miss = (scored - naive_forecast(load, lag_hours).loc[scored.index]).abs()
        by_day_type = miss.groupby(miss.index.dayofweek >= 5).mean()
        print(
            f"{name:<20} average miss {miss.mean():5.1f} kWh "
            f"({miss.mean() / scored.mean():.1%} of average load), "
            f"weekdays {by_day_type[False]:.1f}, weekends {by_day_type[True]:.1f}"
        )


if __name__ == "__main__":
    main()
